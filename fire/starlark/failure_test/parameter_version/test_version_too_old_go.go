package main

import (
	params "fire/starlark/failure_test/parameter_version/test_params"
)

func main() {
	// Parameter is at version 2, but we request version 3
	// This should panic
	value := params.TestValue(3)
	println("Value:", value)
}
