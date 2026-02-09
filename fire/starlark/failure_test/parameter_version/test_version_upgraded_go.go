package main

// Import package which contains both v1 and v2.
// TestValueV1 has a Deprecated doc comment.
import (
	tp "fire/starlark/failure_test/parameter_version/test_params_go"
)

func main() {
	// v1 still works but go vet should flag the deprecated comment
	println("Value:", tp.TestValueMpsV1)
}
