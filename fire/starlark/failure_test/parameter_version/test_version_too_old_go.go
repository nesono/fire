package main

// This import works but TestValueV3 doesn't exist in the package
// (max version is v2), so this should fail to compile.
import (
	tp "fire/starlark/failure_test/parameter_version/test_params_go"
)

func main() {
	println("Value:", tp.TestValueV3)
}
