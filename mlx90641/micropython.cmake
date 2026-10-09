# Module utilisateur MicroPython : MLX90641 (camera IR 16x12)
#
# Arborescence attendue :
#   mlx90641/
#   ├── micropython.cmake
#   ├── mlx90641_mod.c
#   └── lib/
#       ├── MLX90641_API.c
#       ├── MLX90641_API.h
#       └── MLX90641_I2C_Driver.h
#
# Ne PAS compiler MLX90641_I2C_Driver.c : le driver I2C est
# reimplemente dans mlx90641_mod.c via machine.I2C.
#
# Compilation (ESP32) :
#   cd micropython/ports/esp32
#   make BOARD=ESP32_GENERIC USER_C_MODULES=/chemin/absolu/mlx90641/micropython.cmake

add_library(usermod_mlx90641 INTERFACE)

target_sources(usermod_mlx90641 INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/mlx90641_mod.c
    ${CMAKE_CURRENT_LIST_DIR}/lib/MLX90641_API.c
)

target_include_directories(usermod_mlx90641 INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/lib
)

# La librairie Melexis utilise math.h (flottants)
target_compile_options(usermod_mlx90641 INTERFACE
    -Wno-error=unused-variable
    -Wno-error=unused-function
)

target_link_libraries(usermod INTERFACE usermod_mlx90641)
