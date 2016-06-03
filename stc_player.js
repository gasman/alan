(function() {

	var endianTestBuffer = new ArrayBuffer(2);
	var endianTestUint16 = new Uint16Array(endianTestBuffer);
	var endianTestUint8 = new Uint8Array(endianTestBuffer);
	endianTestUint16[0] = 0x0100;
	var isBigEndian = (endianTestUint8[0] == 0x01);

	var registerBuffer = new ArrayBuffer(26);
	/* Expose registerBuffer as both register pairs and individual registers */
	var rp = new Uint16Array(registerBuffer);
	var r = new Uint8Array(registerBuffer);

	var BC = 1, DE = 2, HL = 3, IX = 4, IY = 5;

	var A, B, C, D, E, H, L, IXH, IXL, IYH, IYL;
	if (isBigEndian) {
		A = 0;
		B = 2; C = 3;
		D = 4; E = 5;
		H = 6; L = 7;
		IXH = 8; IXL = 9;
		IYH = 10; IYL = 11;
	} else {
		A = 1;
		B = 3; C = 2;
		D = 5; E = 4;
		H = 7; L = 6;
		IXH = 9; IXL = 8;
		IYH = 11; IYL = 10;
	}

	mem = new Uint8Array(0x10000);

	var ayRegisters = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false];
	var selectedAYRegister = 0;
	function out(port, val) {
		if ((port & 0xc002) == 0xc000) {
			/* AY register select */
			selectedAYRegister = val;
		} else if ((port & 0xc002) == 0x8000) {
			/* AY register write */
			ayRegisters[selectedAYRegister] = val;
			if (selectedAYRegister == 13) ayRegisters[14] = true;
		}
	}

	var dataAddr;
	var positionsTable, w4072, w4074, w4076;
	var songLength, nextPositionNum, height;
	var tempo, tempoCounter;

	var patternPtrs = new Uint16Array(3);
	var ayRegBuffer = new Uint16Array(0x0e);

	function r4000() {
		/*
		Inputs: []
		Outputs: []
		Overwrites: ['D', 'zFlag', 'cFlag', 'sFlag', 'H', 'L', 'A', 'E', 'pvFlag', 'B', 'C']
		*/
		rp[HL] = dataAddr = 0x443c;
		/* DI */
		tempo = mem[dataAddr];
		rp[HL]++;
		rp[DE] = readPointer();
		songLength = mem[rp[DE]] + 1;
		positionsTable = rp[DE] + 1;
		w4072 = readPointer();
		w4074 = readPointer();
		w4076 = dataAddr + 0x001b;

		patternPtrs[0] = 0x4081;
		for (var i = 0x4082; i < 0x4082 + 0x002c; i++) {
			mem[i] = 0;
		}
		nextPositionNum = 0;

		rp[HL] = scan(w4072, 0x0021, 0x00) + 1;
		mem[0x408b] = 0xff;
		mem[0x4095] = 0xff;
		mem[0x409f] = 0xff;
		tempoCounter = 0x01;
		mem[0x4089] = r[L]; mem[0x408a] = r[H];
		mem[0x4093] = r[L]; mem[0x4094] = r[H];
		mem[0x409d] = r[L]; mem[0x409e] = r[H];
		writeAY();
		/* EI */
		return;
	}

	function r4006() {
		/*
		Inputs: ['cFlag']
		Outputs: []
		Overwrites: ['zFlag', 'cFlag', 'sFlag', 'H', 'IXL', 'L', 'A', 'pvFlag', 'B', 'C', 'IXH']
		*/
		var chanPtr;
		var sampleIndex;

		tempoCounter--;
		if (tempoCounter === 0x00) {
			tempoCounter = tempo;
			chanPtr = 0x4084;
			if (advanceMysteryCounter(chanPtr)) {
				if (mem[patternPtrs[0]] == 0xff) newPosition();
				patternPtrs[0] = fetchPatternData(chanPtr, patternPtrs[0]);
			}
			chanPtr = 0x408e;
			if (advanceMysteryCounter(chanPtr)) {
				patternPtrs[1] = fetchPatternData(chanPtr, patternPtrs[1]);
			}
			chanPtr = 0x4098;
			if (advanceMysteryCounter(chanPtr)) {
				patternPtrs[2] = fetchPatternData(chanPtr, patternPtrs[2]);
			}
		}
		chanPtr = 0x4084;
		r4235(chanPtr);
		sampleIndex = r[C];
		getSampleData(mem[chanPtr + 3] | (mem[chanPtr + 4] << 8), sampleIndex);
		ayRegBuffer[0x07] = (r[C] | r[B]) >> 1;
		r[A] = mem[chanPtr + 0x07] + 1;
		if (r[A] !== 0x00) {
			setNoiseReg(r[C], r[H]);
			r[A] = r[L];
			rp[HL] = getTone(chanPtr, rp[DE], sampleIndex);
			ayRegBuffer[0x00] = r[L]; ayRegBuffer[0x01] = r[H];
		}
		ayRegBuffer[0x08] = r[A];
		r4271(chanPtr, 0x08);

		chanPtr = 0x408e;
		r4235(chanPtr);
		r[A] = mem[chanPtr + 0x07] + 1;
		if (r[A] !== 0x00) {
			sampleIndex = r[C];
			getSampleData(mem[chanPtr + 3] | (mem[chanPtr + 4] << 8), sampleIndex);
			ayRegBuffer[0x07] |= r[C] | r[B];
			setNoiseReg(r[C], r[H]);
			r[A] = r[L];
			rp[HL] = getTone(chanPtr, rp[DE], sampleIndex);
			ayRegBuffer[0x02] = r[L]; ayRegBuffer[0x03] = r[H];
		}
		ayRegBuffer[0x09] = r[A];
		r4271(chanPtr, 0x09);

		chanPtr = 0x4098;
		r4235(chanPtr);
		r[A] = mem[chanPtr + 0x07] + 1;
		if (r[A] !== 0x00) {
			sampleIndex = r[C];
			getSampleData(mem[chanPtr + 3] | (mem[chanPtr + 4] << 8), sampleIndex);
			r[C] = (r[C] << 1);
			r[B] = (r[B] << 1);
			ayRegBuffer[0x07] |= r[C] | r[B];
			setNoiseReg(r[C], r[H]);
			r[A] = r[L];
			rp[HL] = getTone(chanPtr, rp[DE], sampleIndex);
			ayRegBuffer[0x04] = r[L]; ayRegBuffer[0x05] = r[H];
		}
		ayRegBuffer[0x0a] = r[A];
		r4271(chanPtr, 0x0a);

		writeAY();
	}

	function readPointer() {
		/*
		Read a pointer from address HL, advance HL,
		and return the pointer converted to an address

		Inputs: ['H', 'L']
		Outputs: ['D', 'E', 'H', 'C', 'L']
		Overwrites: ['D', 'cFlag', 'H', 'L', 'E', 'B', 'C']
		*/
		r[E] = mem[rp[HL]];
		rp[HL]++;
		r[D] = mem[rp[HL]];
		rp[HL]++;

		return rp[DE] + dataAddr;
	}

	function scan(addr, len, id) {
		/*
		Scan through a table of records, starting from 'addr' and each 'len' bytes long,
		for one beginning with byte 'id'. Return its address.

		Inputs: ['A', 'B', 'H', 'C', 'L']
		Outputs: ['H', 'L']
		Overwrites: ['pvFlag', 'cFlag', 'zFlag', 'sFlag', 'H', 'L']
		*/
		while (mem[addr] != id) {
			addr += len;
		}
		return addr;
	}

	function writeAY() {
		/*
		Inputs: ['A']
		Outputs: []
		Overwrites: ['cFlag', 'zFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'B', 'C']
		*/
		var reg = 0x0d;
		if (ayRegBuffer[reg] === 0) {
			reg -= 0x03;
		}
		do {
			out(0xfffd, reg);
			out(0xbffd, ayRegBuffer[reg]);
			reg--;
		} while (reg >= 0);
		rp[BC] = 0xbffd;  // WHY?!?
	}

	function advanceMysteryCounter(chanPtr) {
		/*
		Inputs: ['IXL', 'IXH']
		Outputs: ['sFlag']
		Overwrites: ['sFlag', 'A', 'zFlag', 'pvFlag']
		*/
		mem[chanPtr + 0x02]--;
		if (mem[chanPtr + 0x02] & 0x80) {
			/* mystery counter looped */
			mem[chanPtr + 0x02] = mem[chanPtr - 0x01];
			return true;
		} else {
			return false;
		}
	}

	function newPosition() {
		/*
		Inputs: []
		Outputs: ['C']
		Overwrites: ['D', 'cFlag', 'zFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'E', 'B', 'C']
		*/
		var positionNum = nextPositionNum;
		if (nextPositionNum >= songLength) {
			nextPositionNum = 0x00;
			positionNum = 0x00;
		}
		nextPositionNum++;
		var positionPtr = (positionNum << 1) + positionsTable;
		var patternId = mem[positionPtr];
		r[C] = patternId; // apparently needed...
		height = mem[positionPtr + 1];
		rp[HL] = scan(w4074, 0x0007, patternId) + 1;
		patternPtrs[0] = readPointer();
		patternPtrs[1] = readPointer();
		patternPtrs[2] = readPointer();
	}

	function fetchPatternData(chanPtr, patternPtr) {
		/*
		Inputs: ['IXL', 'IXH', 'H', 'L']
		Outputs: ['H', 'C', 'cFlag', 'L']
		Overwrites: ['zFlag', 'cFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'B', 'C']
		*/
		var pushedHL;
		while (true) {
			var command = mem[patternPtr];
			if (command < 0x60) {
				mem[chanPtr + 0x01] = command;
				mem[chanPtr + 0x00] = 0x00;
				mem[chanPtr + 0x07] = 0x20;
				patternPtr++;
				return patternPtr;
			} else if (command < 0x70) {
				command -= 0x60;
				rp[BC] = 0x0063; /* seemingly needed... */
				rp[HL] = scan(w4076, 0x0063, command) + 1;
				mem[chanPtr + 0x03] = r[L];
				mem[chanPtr + 0x04] = r[H];
				patternPtr++;
			} else if (command < 0x80) {
				command -= 0x70;
				r41f6(chanPtr, command);
				patternPtr++;
			} else if (command == 0x80) {
				patternPtr++;
				mem[chanPtr + 0x07] = 0xff;
				return patternPtr;
			} else if (command == 0x81) {
				patternPtr++;
				return patternPtr;
			} else if (command == 0x82) {
				r41f6(chanPtr, 0x00);
				patternPtr++;
			} else if (command < 0x8f) {
				command -= 0x80;
				ayRegBuffer[0x0d] = command;
				patternPtr++;
				ayRegBuffer[0x0b] = mem[patternPtr];
				patternPtr++;
				mem[chanPtr - 0x02] = 0x01;
				rp[HL] = scan(w4072, 0x0021, 0x00) + 1;
				mem[chanPtr + 0x05] = r[L];
				mem[chanPtr + 0x06] = r[H];
			} else {
				command = (command - 0xa1) & 0xff;
				mem[chanPtr + 0x02] = command;
				mem[chanPtr - 0x01] = command;
				patternPtr++;
			}
		}
	}

	function r41f6(chanPtr, id) {
		rp[HL] = scan(w4072, 0x0021, id) + 1;
		mem[chanPtr + 0x05] = r[L];
		mem[chanPtr + 0x06] = r[H];
		mem[chanPtr - 0x02] = 0x00;
	}

	function r4235(chanPtr) {
		/*
		Inputs: ['IXL', 'cFlag', 'IXH']
		Outputs: ['H', 'C', 'cFlag', 'L']
		Overwrites: ['D', 'zFlag', 'cFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'E', 'C']
		*/
		var a;

		a = (mem[chanPtr + 0x07] + 1) & 0xff;
		if (a === 0x00) return;
		a = (a - 2) & 0xff;
		var aWasZero = (a === 0x00);
		mem[chanPtr + 0x07] = a;

		a = mem[chanPtr + 0x00];
		r[C] = a;
		mem[chanPtr + 0x00] = (a + 1) & 0x1f;
		if (!aWasZero) return;

		var addr = (mem[chanPtr + 0x03] | (mem[chanPtr + 0x04] << 8)) + 0x0060;
		a = (mem[addr] - 1) & 0xff;
		if (a & 0x80) {
			mem[chanPtr + 0x07] = 0xff;
		} else {
			r[C] = a;
			mem[chanPtr + 0x00] = (a + 1) & 0x1f;
			mem[chanPtr + 0x07] = mem[addr + 1] + 1;
		}
	}

	function getSampleData(samplePtr, index) {
		/*
		Inputs: ['A', 'IXL', 'IXH']
		Outputs: ['D', 'H', 'IXL', 'L', 'E', 'B', 'C', 'IXH']
		Overwrites: ['D', 'cFlag', 'zFlag', 'sFlag', 'IXL', 'H', 'L', 'E', 'A', 'pvFlag', 'B', 'C', 'IXH']
		*/
		var a;

		samplePtr += (index * 3) & 0xff;

		a = mem[samplePtr + 0x01];
		r[C] = (a & 0x80) ? 0x10 : 0x00;
		r[B] = (a & 0x40) ? 0x02 : 0x00;
		r[H] = a & 0x1f;
		r[E] = mem[samplePtr + 0x02];

		a = mem[samplePtr + 0x00];
		r[D] = a >> 4;
		r[L] = a & 0x0f;
		if (mem[samplePtr + 0x01] & 0x20) {
			r[D] |= 0x10;
		}
	}

	function setNoiseReg(mask, val) {
		/*
		Apply noise values to AY registers. If C (noise mask) is zero, write H (noise value) to AY reg 6.

		Inputs: ['H', 'C']
		Outputs: ['pvFlag', 'zFlag', 'cFlag', 'sFlag']
		Overwrites: ['A', 'pvFlag', 'cFlag', 'zFlag', 'sFlag']
		*/
		if (mask === 0) {
			ayRegBuffer[0x06] = val;
		}
	}

	var toneTable = new Uint16Array([
		0x0ef8, 0x0e10, 0x0d60, 0x0c80, 0x0bd8, 0x0b28, 0x0a88, 0x09f0,
		0x0960, 0x08e0, 0x0858, 0x07e0, 0x077c, 0x0708, 0x06b0, 0x0640,
		0x05ec, 0x0594, 0x0544, 0x04f8, 0x04b0, 0x0470, 0x042c, 0x03f0,
		0x03be, 0x0384, 0x0358, 0x0320, 0x02f6, 0x02ca, 0x02a2, 0x027c,
		0x0258, 0x0238, 0x0216, 0x01f8, 0x01df, 0x01c2, 0x01ac, 0x0190,
		0x017b, 0x0165, 0x0151, 0x013e, 0x012c, 0x011c, 0x010b, 0x00fc,
		0x00ef, 0x00e1, 0x00d6, 0x00c8, 0x00bd, 0x00b2, 0x00a8, 0x009f,
		0x0096, 0x008e, 0x0085, 0x007e, 0x0077, 0x0070, 0x006b, 0x0064,
		0x005e, 0x0059, 0x0054, 0x004f, 0x004b, 0x0047, 0x0042, 0x003f,
		0x003b, 0x0038, 0x0035, 0x0032, 0x002f, 0x002c, 0x002a, 0x0027,
		0x0025, 0x0023, 0x0021, 0x001f, 0x001d, 0x001c, 0x001a, 0x0019,
		0x0017, 0x0016, 0x0015, 0x0013, 0x0012, 0x0011, 0x0010, 0x000f
	]);

	function getTone(chanPtr, samplePitch, sampleIndex) {
		/*
		Inputs: ['D', 'cFlag', 'zFlag', 'sFlag', 'IXL', 'L', 'E', 'pvFlag', 'IXH']
		Outputs: ['A', 'H', 'cFlag', 'L']
		Overwrites: ['D', 'cFlag', 'zFlag', 'sFlag', 'H', 'L', 'A', 'E', 'pvFlag']
		*/
		var ornPtr = (mem[chanPtr + 0x05] | (mem[chanPtr + 0x06] << 8)) + sampleIndex;
		var note = (mem[chanPtr + 0x01] + mem[ornPtr] + height) & 0x7f;

		var tone = toneTable[note];

		if (samplePitch & 0x1000) {
			return tone + (samplePitch & 0x0fff);
		} else {
			return tone - samplePitch;
		}
	}

	function r4271(chanPtr, volReg) {
		/*
		Inputs: ['IXL', 'IXH', 'H', 'L']
		Outputs: ['A', 'cFlag']
		Overwrites: ['zFlag', 'cFlag', 'sFlag', 'A', 'pvFlag']
		*/
		if (mem[chanPtr + 0x07] == 0xff) return;
		var v = mem[chanPtr - 0x02];
		if (v === 0) {
			return;
		} else if (v == 0x02) {
			ayRegBuffer[0x0d] = 0x00;
		} else {
			mem[chanPtr - 0x02] = 0x02;
		}
		ayRegBuffer[volReg] |= 0x10;
	}

	function gotData(stc) {
		var STCPlayerBin = new Uint8Array([33,60,68,195,9,64,195,68,65,243,126,50,120,64,34,187,64,35,205,181,64,26,19,60,50,122,64,237,83,112,64,205,181,64,237,83,114,64,213,205,181,64,237,83,116,64,33,27,0,205,186,64,235,34,118,64,33,129,64,34,123,64,33,130,64,17,131,64,1,44,0,112,237,176,225,1,33,0,175,205,175,64,61,50,139,64,50,149,64,50,159,64,62,1,50,121,64,35,34,137,64,34,147,64,34,157,64,205,31,68,251,201,119,241,143,241,19,242,94,238,6,1,12,69,231,184,105,87,106,255,0,0,0,0,0,0,0,144,241,255,0,0,0,0,0,0,0,144,241,255,0,0,0,0,0,0,0,144,241,255,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,190,200,9,195,175,64,94,35,86,35,235,1,67,238,9,235,201,22,0,95,135,131,95,221,25,221,126,1,203,127,14,16,194,211,64,74,203,119,6,2,194,219,64,66,230,31,103,221,94,2,221,126,0,245,230,240,15,15,15,15,87,241,230,15,111,221,203,1,110,200,203,226,201,58,160,64,79,33,122,64,190,218,5,65,175,79,60,50,160,64,105,38,0,41,237,91,112,64,25,78,35,126,50,68,67,121,42,116,64,1,7,0,205,175,64,35,205,181,64,237,83,123,64,205,181,64,237,83,125,64,205,181,64,237,83,127,64,201,221,53,2,240,221,126,255,221,119,2,201,58,121,64,61,50,121,64,194,142,66,58,120,64,50,121,64,221,33,132,64,205,57,65,242,111,65,42,123,64,126,60,204,248,64,42,123,64,205,152,65,34,123,64,221,33,142,64,205,57,65,242,130,65,42,125,64,205,152,65,34,125,64,221,33,152,64,205,57,65,242,142,66,42,127,64,205,152,65,34,127,64,195,142,66,126,254,96,218,198,65,254,112,218,211,65,254,128,218,244,65,202,235,65,254,129,202,209,65,254,130,202,241,65,254,143,218,16,66,214,161,221,119,2,221,119,255,35,195,152,65,221,119,1,221,54,0,0,221,54,7,32,35,201,214,96,229,1,99,0,42,118,64,205,175,64,35,221,117,3,221,116,4,225,35,195,152,65,35,221,54,7,255,201,175,24,2,214,112,229,1,33,0,42,114,64,205,175,64,35,221,117,5,221,116,6,221,54,254,0,225,35,195,152,65,214,128,50,174,64,35,126,35,50,172,64,221,54,254,1,229,175,1,33,0,42,114,64,205,175,64,35,221,117,5,221,116,6,225,195,152,65,221,126,7,60,200,61,61,221,119,7,245,221,126,0,79,60,230,31,221,119,0,241,192,221,94,3,221,86,4,33,96,0,25,126,61,250,236,65,79,60,230,31,221,119,0,35,126,60,221,119,7,201,121,183,192,124,50,167,64,201,221,126,7,60,200,221,126,254,183,200,254,2,202,135,66,221,54,254,2,195,139,66,175,50,174,64,203,230,201,221,33,132,64,205,53,66,121,50,60,67,221,42,135,64,205,192,64,121,176,15,50,168,64,221,33,132,64,221,126,7,60,202,186,66,205,105,66,205,50,67,34,161,64,33,169,64,119,205,113,66,221,33,142,64,205,53,66,221,126,7,60,202,239,66,121,50,60,67,221,42,145,64,205,192,64,58,168,64,177,176,50,168,64,205,105,66,221,33,142,64,205,50,67,34,163,64,33,170,64,119,205,113,66,221,33,152,64,205,53,66,221,126,7,60,202,40,67,121,50,60,67,221,42,155,64,205,192,64,58,168,64,203,1,203,0,176,177,50,168,64,205,105,66,221,33,152,64,205,50,67,34,165,64,33,171,64,119,205,113,66,195,31,68,125,245,213,221,110,5,221,102,6,17,10,0,25,221,126,1,134,198,0,135,95,22,0,33,95,67,25,94,35,86,235,209,241,203,98,40,4,203,162,25,201,167,237,82,201,248,14,16,14,96,13,128,12,216,11,40,11,136,10,240,9,96,9,224,8,88,8,224,7,124,7,8,7,176,6,64,6,236,5,148,5,68,5,248,4,176,4,112,4,44,4,240,3,190,3,132,3,88,3,32,3,246,2,202,2,162,2,124,2,88,2,56,2,22,2,248,1,223,1,194,1,172,1,144,1,123,1,101,1,81,1,62,1,44,1,28,1,11,1,252,0,239,0,225,0,214,0,200,0,189,0,178,0,168,0,159,0,150,0,142,0,133,0,126,0,119,0,112,0,107,0,100,0,94,0,89,0,84,0,79,0,75,0,71,0,66,0,63,0,59,0,56,0,53,0,50,0,47,0,44,0,42,0,39,0,37,0,35,0,33,0,31,0,29,0,28,0,26,0,25,0,23,0,22,0,21,0,19,0,18,0,17,0,16,0,15,0,33,174,64,175,182,62,13,32,5,214,3,43,43,43,14,253,6,255,237,121,6,191,237,171,61,242,47,68,201]);
		/* load STC player at address 0x4000 */
		for (var i = 0; i < STCPlayerBin.length; i++) {
			mem[0x4000 + i] = STCPlayerBin[i];
		}
		/* load STC data at address 0x443c */
		for (i = 0; i < stc.length; i++) {
			mem[0x443c + i] = stc[i];
		}

		r4000();
		for (var frame = 0; frame < 10000; frame++) {
			ayRegisters[14] = false;
			r4006();
			console.log(ayRegisters.slice());
		}
	}

	if (typeof(XMLHttpRequest) !== 'undefined') {
		var request = new XMLHttpRequest();

		request.addEventListener('error', function(e) {
			console.log('XHR error', e);
		});

		request.addEventListener('load', function(e) {
			data = request.response;
			var stc = new Uint8Array(data);
			gotData(stc);
		});

		/* trigger XHR */
		request.open('GET', '/shatners_bassoon.stc', true);
		request.responseType = "arraybuffer";
		request.send();
	} else {
		var fs = require('fs');
		fs.readFile(process.argv[2], function(err, data) {
			gotData(data);
		});
	}

})();
