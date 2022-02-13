#include "lib2.h"

#include <Arduino.h>

namespace lib2 {

void foo() {
	SERIAL_IFACE.println("Entering lib2::foo()");
}
	
}  // namespace lib2
