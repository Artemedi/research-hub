"""Exercise only the pinned Julia-1 probability presentation function, without model inference."""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('probabilities', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = [([.955, .044, .001], [1., 0., 0.]),
         ([.951, .049], [.951, .049]),
         ([.6, .395, .005], [.6030150753768844, .3969849246231156, 0.])]
for input_values, expected in cases:
    actual = module.display_probabilities(input_values)
    assert len(actual) == len(expected) and all(abs(a-b) < 1e-12 for a, b in zip(actual, expected))
    print(input_values, '->', actual)
print('3/3 presentation fixtures passed; model inference NOT_RUN')
