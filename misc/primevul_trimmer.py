cwe_top25_2023 = [
    'CWE-787',  # Out-of-bounds Write
    'CWE-79',   # Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')
    'CWE-89',   # SQL Injection
    'CWE-416',  # Use After Free
    'CWE-78',   # Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
    'CWE-20',   # Improper Input Validation
    'CWE-125',  # Out-of-bounds Read
    'CWE-22',   # Path Traversal
    'CWE-352',  # Cross-Site Request Forgery (CSRF)
    'CWE-434',  # Unrestricted Upload of File with Dangerous Type
    'CWE-862',  # Missing Authorization
    'CWE-476',  # NULL Pointer Dereference
    'CWE-287',  # Improper Authentication
    'CWE-190',  # Integer Overflow or Wraparound
    'CWE-502',  # Deserialization of Untrusted Data
    'CWE-77',   # Improper Neutralization of Special Elements used in a Command ('Command Injection')
    'CWE-119',  # Improper Restriction of Operations within the Bounds of a Memory Buffer ('Buffer Overflow')
    'CWE-798',  # Use of Hard-coded Credentials
    'CWE-918',  # Server-Side Request Forgery (SSRF)
    'CWE-306',  # Missing Authentication for Critical Function
    'CWE-362',  # Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition')
    'CWE-269',  # Improper Privilege Management
    'CWE-94',   # Improper Control of Generation of Code ('Code Injection')
    'CWE-863',  # Improper Authorization
    'CWE-276',  # Incorrect Default Permissions
]

cwe_buffer_overflows = []
# cwe_buffer_overflows = [
#     'CWE-119',  # Improper Restriction of Operations within the Bounds of a Memory Buffer (Buffer Overflow)
#     'CWE-120',  # Buffer Copy without Checking Size of Input ('Classic' Buffer Overflow)
#     'CWE-121',  # Stack-based Buffer Overflow
#     'CWE-122',  # Heap-based Buffer Overflow
#     'CWE-124',  # Buffer Underwrite (Buffer Overflow)
#     'CWE-126',  # Buffer Over-read
#     'CWE-127',  # Buffer Under-read
#     'CWE-189',  # Direct Access to Critical Variable via Buffer Overflow
#     'CWE-190',  # Integer Overflow or Wraparound (can lead to buffer overflows in certain conditions)
#     'CWE-191',  # Integer Underflow (Buffer Overflow vulnerability possible)
#     'CWE-194',  # Unexpected Sign Extension (leading to buffer overflow)
#     'CWE-195',  # Signed to Unsigned Conversion Error (leading to buffer overflow)
#     'CWE-202',  # Signal Handler Buffer Overflow
#     'CWE-205',  # Buffer Overflow in Multi-Threaded Program
#     'CWE-209',  # Improper Input Validation (leading to buffer overflow)
#     'CWE-252',  # Unchecked Return Value from a Library (can result in buffer overflow)
#     'CWE-253',  # Reliance on Incorrect or Risky Default Values
#     'CWE-287',  # Improper Authentication (leading to buffer overflow in some cases)
#     'CWE-788',  # Access to Critical Private Variable via Buffer Overflow
#     'CWE-789',  # Uncontrolled Memory Allocation (leading to buffer overflow)
#     'CWE-805',  # Buffer Access with Incorrect Length Value
#     'CWE-1217'  # Insecure Network Buffer Overflow
# ]

cwe_outside_buffer = []
# cwe_outside_buffer = [
#     'CWE-119',  # Improper Restriction of Operations within the Bounds of a Memory Buffer (Buffer Overflow)
#     'CWE-120',  # Buffer Copy without Checking Size of Input ('Classic' Buffer Overflow)
#     'CWE-125',  # Out-of-bounds Read
#     'CWE-126',  # Buffer Over-read
#     'CWE-127',  # Buffer Under-read
#     'CWE-131',  # Incorrect Calculation of Buffer Size
#     'CWE-134',  # Use of Externally-Controlled Format String (which can lead to out-of-bounds read/write)
#     'CWE-170',  # Improper Null Termination (leading to out-of-bounds read)
#     'CWE-194',  # Unexpected Sign Extension (leading to out-of-bounds read/write)
#     'CWE-195',  # Signed to Unsigned Conversion Error (leading to out-of-bounds access)
#     'CWE-208',  # Exposure of Sensitive Information through a Program (out-of-bounds read)
#     'CWE-247',  # Reliance on Insecure Components (may result in out-of-bounds access)
#     'CWE-787',  # Out-of-bounds Write
#     'CWE-788',  # Access to Critical Private Variable via Buffer Overflow (leading to out-of-bounds access)
#     'CWE-819',  # Response Splitting (which can cause out-of-bounds memory access in some cases)
#     'CWE-1200', # Improper Validation of Array Access (leading to out-of-bounds)
# ]

cwe_null_ptr_dereference = []
# cwe_null_ptr_dereference = [
#     'CWE-476',  # NULL Pointer Dereference
#     'CWE-476a', # Dereferencing a null pointer due to missing validation
#     'CWE-476b', # NULL pointer dereference due to improper pointer checks
#     'CWE-578',  # Incorrect Access to Pointer in Dereferencing Context
#     'CWE-674',  # Uncontrolled Resource Consumption (can lead to pointer dereferencing issues)
#     'CWE-715',  # Dereference of Unknown Pointer in String Processing
#     'CWE-264',  # Use of Null Pointer in String Handling Functions
#     'CWE-419',  # Dereferencing a freed pointer that is NULL
#     'CWE-170',  # Improper Null Termination (leading to pointer dereferencing issues)
#     'CWE-772',  # Missing Release of Resource after Use (leading to NULL dereferencing)
#     'CWE-120',  # Buffer Copy without Checking Size of Input ('Classic' null-pointer dereference risk)
#     'CWE-125',  # Out-of-bounds Read/Write (NULL Pointer dereference due to invalid memory access)
#     'CWE-438',  # Incorrect Dereference of NULL Pointer (Explicit check for NULL required)
#     'CWE-539',  # Use of NULL pointer as resource value
#     'CWE-704',  # Incorrect Use of Pointer Dereferencing Based on Content (NULL dereference risk)
# ]


import json

cwes = list(set(cwe_top25_2023 + cwe_buffer_overflows + cwe_outside_buffer + cwe_null_ptr_dereference))

f = open(r'D:\grad_research_2\datasets\PrimeVul\primevul_train_paired.jsonl', 'r')
f2 = open(r'D:\grad_research_2\datasets\filtered_primevul_train_paired.jsonl', 'w+')
samples = f.readlines()
samples = [json.loads(sample) for sample in samples]
for sample in samples:
    if any(val in cwes for val in sample.get('cwe', [])):
        f2.write(json.dumps(sample) + '\n')
        print(sample.get('idx',''))
f.close()
f2.close()