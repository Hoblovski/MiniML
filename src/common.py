LegalUnaOps = {
        '-',
}

LegalBinOps = {
        '*', '/', '%',
        '+', '-',
        '>', '<', '>=', '<=', '==', '!=',
}

AllBuiltins = {
        'println',
}

LegalBrOps = {
        "br",
        "beqz", "bnez", "beq", "bne",
        "ble", "blt", "bge", "bgt"
}

relStrToOp = {
    'eq': '==', 'ne': '!=', 'gt': '>',
    'ge': '>=', 'lt': '<', 'le': '<='
}
