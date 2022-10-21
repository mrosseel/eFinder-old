# Changelog for eFinder software

## Version 15

[Keith Venables]

- Remove LCD handpad option.
- Add QHY as option for the camera.

## Version 14

[Keith Venables]

- Fixed a bug that prevents handpad saved exposure & gain preferences from being displayed on the GUI.
- Modified how the handpad display starts when using the GUI version.
- Fixed a bug on the handpad version whereby a failed solve could result in the previous delta being displayed without a 'failed solve' warning
- Make the handpad work with the VNC GUI version

[Wim De Meester]

- Move the Nexus code to a class outside of the main classes
- Create a Coordinates class to transform RA and dec to AltAz
- Create a handpad class with all code for the display box
- Create CameraInterface and ASICamera class

## Version 13

[Keith Venables, Wim De Meester]

The clock section in the GUI variant is now a thread and runs nice and smooth. (Wim’s code - Thx)

I’ve pulled out all the Nexus communications into a Class method. On boot the code also determines how it can connect to the Nexus, usb or wifi. Thus these variants aren't needed any more. This will make code changes a lot easier.

For instance the Nexus RA can be obtained by single call
ra = Nexus.get(:GR#)

Some Nexus commands don’t produce a reply, so they are

Nexus.write(:P#)

etc

Nexus.read() produces a grab of all the location and time data from the Nexus.

## Version 12

[Keith Venables]

Biggest recent issue has been the realisation that Skyfield wasn't precessing JNow back to J2000, despite it being described and no errors being thrown. This was messing up the align and local sync functions (adding quite a few arc minutes of error). Also could see that various methods of converting from RA & Dec to AltAz were producing different results.

The fix has been a significant change. The eFinder uses JNow exclusively now internally (solver output being precessed immediately) and my own altAz conversion method applied to all cases for consistency.

The rather neat method of finishing a classic goto, by doing a solve and local sync, followed by repeat goto (aka 'goto++'), wasnt consistent. Now realise that the above issues were partly to blame, plus a discovery that the LX200 protocol used to talk to the Nexus has one “target” used for both align and goto. Easily fixed by reading the goto target before the local sync, and then resending it back to the Nexus as part of the goto++.

This goto++ method seems now to be very consistent. The solve & local sync is very accurate (although Serge has a bug in the Nexus DSC for repeated syncs at the same location) and the goto++ results in scope positioning as good as your drive (ServoCat or ScopeDog) can manage. I’m getting about an arc minute.

The Nexus bug affects everybody with a  Nexus DSC - but not many will have noticed! Repeated local syncs result in the Nexus not quite resetting to the required RA & Dec. Can be 1/10 to 1/3 of a degree off. Without the eFinder most users wouldn’t be aware of the error - except the target wouldn’t be centred in the eyepiece. First local sync in any area of the sky is perfect. Serge is on the case.

For a while I have been using the wcs- modules available with the solver to make the offset measurement and application easier. (Eg the solver can return the RA & Dec of any pixel in the image, not just the centre.

I have now modified the initial offset calibration routine. Just align the main scope with any bright, named star, and the eFinder will recognise it and do the calibration. The offset measured can be saved to disk.

The GUI variant can now show the graticule and eyepiece fov centred or offset, rotated to match the view, and overlayed with object annotations (see example below). The GUI got a make over with night vision colours, and a few more buttons and readouts.

An efinder.config file now holds a lot of user specific set up data, mostly used for the GUI variant. The user can list the eyepieces, exposure & gain choices etc.

I’ve now effectively ditched my LCD hand box and changed to a OLED display in a removable hand box. This has 3 lines of very high contrast text. Looks very similar to the Nexus display. The hand box uses a Pi Pico and is connected to the eFinder via standard USB. Photo below.

Also switched to a build using a standard Raspberry Pi 32bit OS (Debian 10). The astroberry based solver didn’t have all the features (licensing) and also the wifi seems much more stable and robust.

Versions 12_3_ are in the share for those with access. The OLED wifi has what looks like redundant code in it, but it is a new interface to ScopeDog. ScopeDog mk2.1 (not yet released) takes over control of the eFinder as part of the standard alignment and goto actions. No user interface needed!
