# ICM-45686

## Schematic

* A 32.6768 oscillator is connected to INT2(pin9).
* INT1(pin4) is connected to a X10-21(SODIMM_206)

SPI is using
* SPI_MISO is connected to SDO(pin1)
* SPI_MOSI is connected to SDx(pin14)
* SPI_CLK is connected to SCx(pin23)
* SPI_CS is connected to CSB(pin12)

This pins are not connected:
* ASDx(pin2)
* ASCx(pin3)
* OCSB(pin10)
* OSD0(pin11)

## Requirements

* ICM45686_DT_ACCEL_ODR_6400: 6.4kHz
* SPI at 8MHz.
* The IMU should be clocked from the oscillator.

* Once the IMU has been initiated, it should continue continuously sample.
* After the sample is convertet, the IMU signals using INT1.
* The MCU is triggered by INT1 and collects the result using SPI.


## spi-hold-cs

Links

* app_emw/zephyr/prj_verdin_imx8mp.overlay
  Hold CS across the driver's separate address/data bursts.
* https://docs.zephyrproject.org/latest/build/dts/api/bindings/sensor/invensense%2Cicm45686-spi.html
  spi-hold-cs: In some cases, it is necessary for the controller to manage SPI chip select under software control.

Prompt: May we change the setting of 'spi-hold-cs' so that "Hold CS across the driver's separate address/data bursts." is not required anymore.

Claude: Short answer: No — spi-hold-cs can't replace the GPIO CS here, and it would actually make things worse.
