package main

import (
	params "fire/starlark/failure_test/parameter_version/test_params"
)

func main() {
	// Parameter is at version 2, but we request version 1
	// This should print a warning
	value := params.TestValue(1)
	println("Value:", value)
}
