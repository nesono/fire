// Compiles and checks generated C++ for special characters in values and units.

#include "fire/starlark/codegen_test/special_params_cc/acceleration_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/error_rate_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/noise_level_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/ratio_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/resistance_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/special_string_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/special_table_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/temperature_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/thickness_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/turn_rate_v1.h"
#include "fire/starlark/codegen_test/special_params_cc/volume_v1.h"
#include <cstring>
#include <iostream>

namespace {

int failures = 0;

void Check(bool ok, const char *what) {
  if (!ok) {
    std::cerr << "FAILED: " << what << "\n";
    ++failures;
  }
}

// "?\?/" is written with an escaped question mark so that the test source
// itself is not affected by trigraph replacement.
const char *const kExpected = "say \"hi\" \\ back\\\\slash\ttab\nline2 é {x} %s "
                              "$y 'q' /* c */ // not a comment \\u000a \\n ?\?/ \001\177"
                              "end\\";

} // namespace

int main() {
  Check(std::strcmp(SPECIAL_STRING, kExpected) == 0, "special string");

  Check(SPECIAL_TABLE.size() == 2, "table size");
  Check(std::strcmp(SPECIAL_TABLE[0].label, kExpected) == 0, "table string cell");
  Check(std::strcmp(SPECIAL_TABLE[1].label, "plain") == 0, "table plain cell");
  Check(SPECIAL_TABLE[0].temp_degc == -40.5, "table column in degrees celsius");
  Check(SPECIAL_TABLE[0].ratio_percent == 12.5, "table column in percent");
  Check(SPECIAL_TABLE[0].accel_mps2 == 9.81, "table column in m/s squared");
  Check(SPECIAL_TABLE[0].level_dba == 85.0, "table column in dB(A)");

  Check(TEMPERATURE_DEGC == 21.5, "degrees celsius");
  Check(RATIO_PERCENT == 12.5, "percent");
  Check(ACCELERATION_MPS2 == 9.81, "m/s squared");
  Check(NOISE_LEVEL_DBA == 85.0, "dB(A)");
  Check(THICKNESS_UM == 3.0, "micro sign");
  Check(RESISTANCE_OHM == 4.7, "omega");
  Check(VOLUME_M3 == 1.5, "m cubed");
  Check(ERROR_RATE_PERMILLE == 2.5, "per mille");
  Check(TURN_RATE_DEGPS == 90.0, "degrees per second");

  return failures == 0 ? 0 : 1;
}
