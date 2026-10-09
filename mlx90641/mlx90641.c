#include "py/runtime.h"
#include "py/mperrno.h"
#include "py/nlr.h"
#include "MLX90641_API.h"
#include "MLX90641_I2C_Driver.h"

// L'objet machine.I2C reste visible du GC
MP_REGISTER_ROOT_POINTER(mp_obj_t mlx90641_i2c);

#define EMISSIVITY 0.95f
#define TA_SHIFT   8.0f

static uint8_t mlx_addr = 0x33;
static paramsMLX90641 mlx_params;
static uint16_t mlx_ee[832];
static uint16_t mlx_frame[242];
static uint8_t io_buf[2 * 832];

/* ---------- Driver I2C pour la librairie Melexis ---------- */

void MLX90641_I2CInit(void) {}
void MLX90641_I2CFreqSet(int freq) { (void)freq; }  // gérée côté Python

int MLX90641_I2CRead(uint8_t slaveAddr, uint16_t startAddress,
                     uint16_t nMemAddressRead, uint16_t *data) {
    mp_obj_t i2c = MP_STATE_VM(mlx90641_i2c);
    size_t nbytes = nMemAddressRead * 2;
    if (i2c == MP_OBJ_NULL || nbytes > sizeof(io_buf)) return -1;

    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t a[7];
        mp_load_method(i2c, MP_QSTR_readfrom_mem_into, a);
        a[2] = MP_OBJ_NEW_SMALL_INT(slaveAddr);
        a[3] = MP_OBJ_NEW_SMALL_INT(startAddress);
        a[4] = mp_obj_new_bytearray_by_ref(nbytes, io_buf);
        a[5] = MP_OBJ_NEW_QSTR(MP_QSTR_addrsize);
        a[6] = MP_OBJ_NEW_SMALL_INT(16);
        mp_call_method_n_kw(3, 1, a);
        nlr_pop();
    } else {
        return -1;  // OSError Python capturée -> code d'erreur C
    }
    for (size_t i = 0; i < nMemAddressRead; i++) {
        data[i] = (io_buf[2 * i] << 8) | io_buf[2 * i + 1];
    }
    return 0;
}

int MLX90641_I2CWrite(uint8_t slaveAddr, uint16_t writeAddress, uint16_t data) {
    mp_obj_t i2c = MP_STATE_VM(mlx90641_i2c);
    if (i2c == MP_OBJ_NULL) return -1;
    static uint8_t b[2];
    b[0] = data >> 8;
    b[1] = data & 0xFF;

    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t a[7];
        mp_load_method(i2c, MP_QSTR_writeto_mem, a);
        a[2] = MP_OBJ_NEW_SMALL_INT(slaveAddr);
        a[3] = MP_OBJ_NEW_SMALL_INT(writeAddress);
        a[4] = mp_obj_new_bytearray_by_ref(2, b);
        a[5] = MP_OBJ_NEW_QSTR(MP_QSTR_addrsize);
        a[6] = MP_OBJ_NEW_SMALL_INT(16);
        mp_call_method_n_kw(3, 1, a);
        nlr_pop();
        return 0;
    }
    return -1;
}

int MLX90641_I2CGeneralReset(void) {
    mp_obj_t i2c = MP_STATE_VM(mlx90641_i2c);
    if (i2c == MP_OBJ_NULL) return -1;
    static uint8_t cmd = 0x06;
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t a[4];
        mp_load_method(i2c, MP_QSTR_writeto, a);
        a[2] = MP_OBJ_NEW_SMALL_INT(0x00);
        a[3] = mp_obj_new_bytearray_by_ref(1, &cmd);
        mp_call_method_n_kw(2, 0, a);
        nlr_pop();
        return 0;
    }
    return -1;
}

/* ---------- API exposée à Python ---------- */

// mlx90641.init(i2c, addr=0x33)
static mp_obj_t mlx_init(size_t n_args, const mp_obj_t *args) {
    MP_STATE_VM(mlx90641_i2c) = args[0];
    mlx_addr = (n_args > 1) ? mp_obj_get_int(args[1]) : 0x33;
    if (MLX90641_DumpEE(mlx_addr, mlx_ee) != 0) {
        mp_raise_OSError(MP_EIO);
    }
    if (MLX90641_ExtractParameters(mlx_ee, &mlx_params) != 0) {
        mp_raise_ValueError(MP_ERROR_TEXT("EEPROM invalide"));
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mlx_init_obj, 1, 2, mlx_init);

// mlx90641.set_refresh_rate(0..7)  0=0.5Hz 1=1Hz 2=2Hz 3=4Hz 4=8Hz 5=16Hz 6=32Hz 7=64Hz
static mp_obj_t mlx_set_rate(mp_obj_t rate) {
    if (MLX90641_SetRefreshRate(mlx_addr, mp_obj_get_int(rate)) != 0) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(mlx_set_rate_obj, mlx_set_rate);

// mlx90641.read(buf)  -> buf = array('f', 192 valeurs), températures en °C
static mp_obj_t mlx_read(mp_obj_t buf_obj) {
    mp_buffer_info_t bi;
    mp_get_buffer_raise(buf_obj, &bi, MP_BUFFER_WRITE);
    if (bi.len < 192 * sizeof(float)) {
        mp_raise_ValueError(MP_ERROR_TEXT("buffer trop petit (192 floats)"));
    }
    float *out = (float *)bi.buf;
    for (int sp = 0; sp < 2; sp++) {      // 2 sous-pages = image complète
        if (MLX90641_GetFrameData(mlx_addr, mlx_frame) < 0) {
            mp_raise_OSError(MP_EIO);
        }
        float ta = MLX90641_GetTa(mlx_frame, &mlx_params);
        MLX90641_CalculateTo(mlx_frame, &mlx_params, EMISSIVITY, ta - TA_SHIFT, out);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(mlx_read_obj, mlx_read);

static const mp_rom_map_elem_t mlx_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__),          MP_ROM_QSTR(MP_QSTR_mlx90641) },
    { MP_ROM_QSTR(MP_QSTR_init),              MP_ROM_PTR(&mlx_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_refresh_rate),  MP_ROM_PTR(&mlx_set_rate_obj) },
    { MP_ROM_QSTR(MP_QSTR_read),              MP_ROM_PTR(&mlx_read_obj) },
};
static MP_DEFINE_CONST_DICT(mlx_globals, mlx_globals_table);

const mp_obj_module_t mlx90641_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&mlx_globals,
};
MP_REGISTER_MODULE(MP_QSTR_mlx90641, mlx90641_user_cmodule);