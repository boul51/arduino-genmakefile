#include <Arduino.h>

#include "lib1.h"
#include "lib2.h"

void setup()
{
	SERIAL_IFACE.begin(115200);
	while (!SERIAL_IFACE) {}
	SERIAL_IFACE.println("Entering main");
}

void loop()
{
	SERIAL_IFACE.println("MY_STRING: " MY_STRING);
	lib1::foo();
	lib2::foo();
	delay(1000);
}
