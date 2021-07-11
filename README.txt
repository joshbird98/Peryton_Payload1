Team Peryton - Payload

This is internal documentation for the team, however I will publish proper open-source documentation in the future.

* For our actual flight, we opted to replace the GPS circuitry with a loud siren. This gave us a much mre reliable
and robust recovery mechanism. Whislt the hardware schematics show the GPS and LoRa system, no software has
been published.

Our payload acts as both rocket recovery mechanism, and data acquisition. It logs pressure, temperature and 9DoF
motion measurements to a microSD card, at 50 [Hz]. Power it with a LiHV cell, preferably 450mAh.
Sensors used are the BMP280 and MPU9250, many open-source libraries already exist for these ICs.
An ATMEGA328P communicates to the sensors in I2C mode, and to the microSD card in SPI mode.

As well as the hardware and software, I've also written a python script for quick analysis of flight data, useful 
for when you're still in the field. Results from our rocketry flight are also included as an example of what
the payload has achieved.