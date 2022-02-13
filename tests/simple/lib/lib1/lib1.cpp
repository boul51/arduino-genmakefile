#include "lib1.h"

#include <Arduino.h>

namespace lib1 {

void foo() {
	SERIAL_IFACE.println("Entering lib1::foo()");
}
	
}  // namespace lib1
