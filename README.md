
  # Swiss Air Data Decoder
  
## Overview

This Saleae Logic2 high level analyser extension decodes air data frame sent by a module from Simtec AG <https://www.swiss-airdata.com/>. 

It is compatible with the following products: ADES-12, ADP-5.5, PSS8 and PMH air data computer. However it is compatible only with RS485 bus as it can be decoded by the Async Serial analyzer but not with ARINC-429 bus. Details about the format used to send the air data can be found in devices *Interface Control Document*.

The label and the value of the data transmitted are displayed on top of the frame, as shown bellow:

![frame_image](support/frame-parser.png)

In the data table, flag of the data transmitted is also displayed:

![table_full](support/table-all-data.png)

It can be convenient to add a filter on the table to see the time evolution of a specific data:

![table_filter](support/table-filter.png)

**Warning: Only data and status packet are parsed. Commands, such as QNH setting and sensor zeroing are ignored by this extension** 

 ## How to use it

To try this extension out for yourself, you will first need to capture a communication data:

 1. Open Logic 2 (2.3.0 or greater)
 1. Capture a frame sent by an air data computer, pin RS485-A. If you don't have one you can use the provided capture to try this extension [support/example-capture.sal](support/example-capture.sal)
 1. Add an *Async Serial* analyser, with the following configuration
    - Bit rate : depends on the configuration
    - Bits per frame: 8
    - Stop Bits: 1
    - Parity Bit: No parity
    - Significant bit: Least significant bit sent first
    - Signal inversion: Non inverted
    - Mode: Normal
 1. Add the *Air Data - Simtec*  analyser. Select the *Async Serial* as input analyser

 ## Notes

Tested with Logic 2, version 2.3.26

This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Simtec AG has no obligation to provide maintenance, support,  updates, enhancements, or modifications.