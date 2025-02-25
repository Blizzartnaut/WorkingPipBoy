Component List will be given after its finalized.
#Component list here
https://suptronics.com/miniPCkits/x728.html

https://shop.sb-components.co.uk/products/gps-hat-for-raspberry-pi?srsltid=AfmBOorg9ltRbocOCu-m2uV9KkdGrXocV9QHlCmNxTUOFLs0BwyfUn6d
https://github.com/sbcshop/GPS-Hat-for-Raspberry-Pi/blob/main/README.md

https://www.adafruit.com/product/2130

https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/CDS-40304-L1003/9699445?_gl=1*1qpcunr*_up*MQ..*_gs*MQ..&gclid=CjwKCAiA2JG9BhAuEiwAH_zf3riu03ec3nWH169lawSwrJrGfQTaxeWvGgedwM61h_wg8hIk6gTI3hoCNsAQAvD_BwE&gclsrc=aw.ds

https://learn.adafruit.com/adafruit-pam8302-mono-2-5w-class-d-audio-amplifier/pinouts

(maybe later) https://theelectronicgoldmine.com/products/c7061
https://theelectronicgoldmine.com/collections/geiger-counters

Useful links to activate the subsystems
To activate the power features including battery capacity
https://suptronics.com/miniPCkits/x728-software.html

https://github.com/sbcshop/GPS-Hat-for-Raspberry-Pi

https://pysdr.org/content/pyqt.html #needed for the sdr feature

https://github.com/SensorsIot/Geiger-Counter-RadiationD-v1.1-CAJOE-/tree/master/Geiger_Counter

https://github.com/pyrtlsdr/pyrtlsdr/tree/master


Inspiration for the housing
https://ytec3d.com/pip-boy-3000-mark-iv-assembly/

https://www.therpf.com/forums/threads/pipboy-3000-mk-iv-from-fallout-4-mid-grade.358847/

https://sketchfab.com/3d-models/pip-boy-3000-mark-iv-ed25237501a84af8b65198cc9c32d9da

https://www.therpf.com/forums/threads/functional-pip-boy-3000-mk-iv-from-fallout-4.245034/

https://grabcad.com/library/pip-boy-3000-mark-4-1

For correctly installing libwebp.so.6 follow the following
https://stackoverflow.com/questions/54833807/libwebp-so-6-import-error-in-raspberry-pi-3b

For audio
https://learn.adafruit.com/usb-audio-cards-with-a-raspberry-pi/updating-alsa-config to get the audio to work via usb


How To Install System:

1: on your device open a terminal, 'git clone https://github.com/Blizzartnaut/WorkingPipBoy.git'
(All following commands will be assumed to be in the terminal until otherwise mentioned)
2: python -m venv PipBoyVenv
3: . PipBoyVenv/bin/activate (yes include the period at the beginning of the entry)
4: sudo apt update
5: sudo apt install mlocate
6: sudo updatedb
7: sudo ln -s /usr/lib/aarch64-linux-gnu/libwebp.so.7 /usr/lib/aarch64-linux-gnu/libwebp.so.6 (This only works on bookworm version of raspberry pi 4b as of 02/24/2025, otherwise you will need to find them and symlink them yourself)
8: sudo ln -s /usr/lib/aarch64-linux-gnu/libtiff.so.6 /usr/lib/aarch64-linux-gnu/libtiff.so.5
9: sudo apt-get install librtlsdr-dev
10: make sure to install all components in FullRequirementsLIN.txt and in FullRequirementsPIP.txt, Lin first, then pip.
11: install all music to the music folder for your playlist
12: install all mapping tiles for the mapping folder, a detailed instruction for this may be available at a later date
