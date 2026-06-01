import os
import json
import random
import re

from pathlib import Path
from datetime import datetime

computerId = "b754d0a98986fd3eca2eae4fa8ec9a1f"
key = "10-30-11-80-60-61-21-60-40-41-30-2"
ADD = 0
SUB = 1

def getTime():
	return datetime.now().strftime('%m/%d/%Y %H:%M:%S')

roamingDir = Path(os.environ.get('APPDATA'))
cachePath = roamingDir / "WindowTop" / "cache.json"
settingsPath = roamingDir / "WindowTop" / "settings.json"
print(cachePath)
print(settingsPath)

def loadJson(path):
	try:
		with open(path, 'r', encoding='utf-8-sig') as file:
			return json.load(file)
	except (FileNotFoundError, json.JSONDecodeError):
		RuntimeError()

def saveJson(path, data):
	with open(path, 'w', encoding='utf-8-sig') as file:
		json.dump(data, file, indent="\t")


def verifies(key: str, verbose: bool = False) -> bool:
	"""Python port of the supplied C# verifier."""
	if not key:
		return False

	parts = key.split("-")
	if len(parts) != 12:
		return False

	op = -1
	total = 0

	for i, part in enumerate(parts):
		# The visible C# code calls int.TryParse, so all parts must be integers.
		# This rejects signs too, keeping the key in the same style as the sample.
		if not re.fullmatch(r"\d+", part):
			return False

		num3 = int(part)
		num4 = num3

		# First 11 chunks are divided by 10.
		if i < len(parts) - 1:
			num4 //= 10

		if op != -1:
			if op == 0:
				total += num4
			elif op == 1:
				total -= num4
			elif op == 2:
				total *= num4
			elif op == 3:
				if num4 == 0:
					return False
				# C# int division truncates toward zero.
				total = int(total / num4)
			else:
				total = 0
		else:
			total = num4

		if verbose:
			opname = {0: "+", 1: "-", 2: "*", 3: "/"}.get(num3 % 10, "reset")
			print(
				f"part {i + 1:02}: raw={num3}, value={num4}, "
					f"next_op={num3 % 10} ({opname}), total={total}"
			)

		op = num3 % 10

	return total - 8 <= 1 or total == 3198 or total == 6384


def evaluate_first_11(values: list[int], ops: list[int]) -> int:
	"""
	Evaluate chunks 1..11 only.

	values has 11 items, each 1..9.
	ops has 10 items, each operation between those 11 values.
	"""
	total = values[0]
	for op, value in zip(ops, values[1:]):
		if op == ADD:
			total += value
		elif op == SUB:
			total -= value
		else:
			raise ValueError(f"unsupported op: {op}")
	return total


def generate_key() -> str:
	"""Generate one random compact key that verifies successfully."""
	while True:
		# The first 11 chunks are 2 digits: value digit + operation digit.
		values = [random.randint(1, 9) for _ in range(11)]

		# Operations from chunk 1 through chunk 10. Use only + and - to keep
		# the key compact and avoid division-by-zero edge cases.
		ops_first_10 = [random.choice([ADD, SUB]) for _ in range(10)]
		total_after_11 = evaluate_first_11(values, ops_first_10)

		# Pick whether the full expression should end at 8 or 9.
		target = random.choice([8, 9])

		# The 11th chunk's operation affects the final one-digit chunk.
		possible_last_steps: list[tuple[int, int]] = []

		# If chunk 11 says '+', final_digit must be target - total_after_11.
		final_digit = target - total_after_11
		if 0 <= final_digit <= 9:
			possible_last_steps.append((ADD, final_digit))

		# If chunk 11 says '-', final_digit must be total_after_11 - target.
		final_digit = total_after_11 - target
		if 0 <= final_digit <= 9:
			possible_last_steps.append((SUB, final_digit))

		if not possible_last_steps:
			continue

		op_11, final_digit = random.choice(possible_last_steps)
		ops = ops_first_10 + [op_11]

		chunks = [f"{value}{op}" for value, op in zip(values, ops)]
		chunks.append(str(final_digit))

		key = "-".join(chunks)

		# Sanity checks: same length as the known-working key, and verifies.
		assert len(key) == len("10-10-10-10-10-10-10-10-10-10-11-2")
		assert verifies(key), f"generated invalid key: {key}"
		return key


cache = loadJson(cachePath)
cache["Activation"] = {
	"IsLicenseCached": True,
	"ActivationLastCheckTime": getTime(),
	"LicenseKeyMaxVersionTime": None,
	"LicenseKeyMaxComputers": 5,
	"LicenseKeyMaxUsers": 0,
	"LoginEmail": None,
	"LicenseKeyIssue": "undefined",
	"IsSubscriptionLicenseKey": False,
	"LicenseKeyUnknownIssueCode": None,
	"Validated": True,
	"IsFullVersion": True,
	"IsTrialMode": False,
	"DaysLeft": 0,
	"IsTrialModeAvailable": False,
	"TrialStartDate": None,
}

saveJson(cachePath, cache)

settings = loadJson(settingsPath)
settings["Activation"] = {
	"ComputerId": None,
	"ComputerIdV2": computerId,
	"LicenseKey": generate_key(),
	"ShowTrialExpiredDialog": True,
	"ShowSuggestProVerDialog": True,
}
saveJson(settingsPath, settings)
