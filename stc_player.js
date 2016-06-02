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

	var BC = 1, DE = 2, HL = 3, IX = 4, IY = 5, SP = 6;

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

	var zFlag = false, cFlag = false, sFlag = false, pvFlag = false;

	mem = new Uint8Array(0x10000);
	var tmp;

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

	function r4000() {
		/*
		Inputs: []
		Outputs: []
		Overwrites: ['D', 'zFlag', 'cFlag', 'sFlag', 'H', 'L', 'A', 'E', 'pvFlag', 'B', 'C']
		*/
		rp[HL] = 0x443c;
		/* DI */
		r[A] = mem[rp[HL]];
		mem[0x4078] = r[A];
		mem[0x40bb] = r[L]; mem[0x40bc] = r[H];
		rp[HL]++;
		r40b5();
		r[A] = mem[rp[DE]];
		rp[DE]++;
		r[A]++;
		mem[0x407a] = r[A];
		mem[0x4070] = r[E]; mem[0x4071] = r[D];
		r40b5();
		mem[0x4072] = r[E]; mem[0x4073] = r[D];
		rp[SP]--; mem[rp[SP]] = r[D]; rp[SP]--; mem[rp[SP]] = r[E];
		r40b5();
		mem[0x4074] = r[E]; mem[0x4075] = r[D];
		rp[HL] = 0x001b;
		r40ba();
		rp[HL] = rp[DE];
		mem[0x4076] = r[L]; mem[0x4077] = r[H];
		rp[HL] = 0x4081;
		mem[0x407b] = r[L]; mem[0x407c] = r[H];
		rp[HL] = 0x4082;
		rp[DE] = 0x4083;
		rp[BC] = 0x002c;
		mem[rp[HL]] = r[B];
		while(true) {mem[rp[DE]] = mem[rp[HL]]; rp[DE]++; rp[HL]++; rp[BC]--; if (rp[BC] === 0) break;}
		r[L] = mem[rp[SP]]; rp[SP]++; r[H] = mem[rp[SP]]; rp[SP]++;
		rp[BC] = 0x0021;
		r[A] = 0x00;
		r40af();
		r[A]--;
		mem[0x408b] = r[A];
		mem[0x4095] = r[A];
		mem[0x409f] = r[A];
		r[A] = 0x01;
		mem[0x4079] = r[A];
		rp[HL]++;
		mem[0x4089] = r[L]; mem[0x408a] = r[H];
		mem[0x4093] = r[L]; mem[0x4094] = r[H];
		mem[0x409d] = r[L]; mem[0x409e] = r[H];
		r441f();
		/* EI */
		return;
	}

	function r4006() {
		/*
		Inputs: ['cFlag']
		Outputs: []
		Overwrites: ['zFlag', 'cFlag', 'sFlag', 'H', 'IXL', 'L', 'A', 'pvFlag', 'B', 'C', 'IXH']
		*/
		var pc = 0x4006;
		while (true) {
			switch (pc) {
				case 0x4006:
					pc = 0x4144; break;
				case 0x4144:
					r[A] = mem[0x4079];
					r[A]--; zFlag = (r[A] === 0x00);
					mem[0x4079] = r[A];
					if (!zFlag) {pc = 0x428e; break;}
					r[A] = mem[0x4078];
					mem[0x4079] = r[A];
					rp[IX] = 0x4084;
					r4139();
					if (!sFlag) {pc = 0x416f; break;}
					r[L] = mem[0x407b]; r[H] = mem[0x407c];
					r[A] = mem[rp[HL]];
					zFlag = (r[A] == 0xff);
					if (zFlag) r40f8();
					r[L] = mem[0x407b]; r[H] = mem[0x407c];
					r[L] = mem[0x407b]; r[H] = mem[0x407c];
					r4198();
					mem[0x407b] = r[L]; mem[0x407c] = r[H];
				case 0x416f:
					rp[IX] = 0x408e;
					r4139();
					if (!sFlag) {pc = 0x4182; break;}
					r[L] = mem[0x407d]; r[H] = mem[0x407e];
					r4198();
					mem[0x407d] = r[L]; mem[0x407e] = r[H];
				case 0x4182:
					rp[IX] = 0x4098;
					r4139();
					if (!sFlag) {pc = 0x428e; break;}
					r[L] = mem[0x407f]; r[H] = mem[0x4080];
					r4198();
					mem[0x407f] = r[L]; mem[0x4080] = r[H];
					pc = 0x428e; break;
				case 0x428e:
					rp[IX] = 0x4084;
					r4235();
					r[A] = r[C];
					mem[0x433c] = r[A];
					r[IXL] = mem[0x4087]; r[IXH] = mem[0x4088];
					r40c0();
					r[A] = r[C];
					r[A] |= r[B];
					cFlag = !!(r[A] & 0x01); r[A] = (r[A] >> 1) | (r[A] << 7);
					mem[0x40a8] = r[A];
					rp[IX] = 0x4084;
					r[A] = mem[(rp[IX] + 0x07) & 0xffff];
					r[A]++; zFlag = (r[A] === 0x00);
					if (zFlag) {pc = 0x42ba; break;}
					r4269();
					r4332();
					mem[0x40a1] = r[L]; mem[0x40a2] = r[H];
				case 0x42ba:
					rp[HL] = 0x40a9;
					mem[rp[HL]] = r[A];
					r4271();
					rp[IX] = 0x408e;
					r4235();
					r[A] = mem[(rp[IX] + 0x07) & 0xffff];
					r[A]++; zFlag = (r[A] === 0x00);
					if (zFlag) {pc = 0x42ef; break;}
					r[A] = r[C];
					mem[0x433c] = r[A];
					r[IXL] = mem[0x4091]; r[IXH] = mem[0x4092];
					r40c0();
					r[A] = mem[0x40a8];
					r[A] |= r[C];
					r[A] |= r[B];
					mem[0x40a8] = r[A];
					r4269();
					rp[IX] = 0x408e;
					r4332();
					mem[0x40a3] = r[L]; mem[0x40a4] = r[H];
				case 0x42ef:
					rp[HL] = 0x40aa;
					mem[rp[HL]] = r[A];
					r4271();
					rp[IX] = 0x4098;
					r4235();
					r[A] = mem[(rp[IX] + 0x07) & 0xffff];
					r[A]++; zFlag = (r[A] === 0x00);
					if (zFlag) {pc = 0x4328; break;}
					r[A] = r[C];
					mem[0x433c] = r[A];
					r[IXL] = mem[0x409b]; r[IXH] = mem[0x409c];
					r40c0();
					r[A] = mem[0x40a8];
					r[C] = (r[C] << 1) | (r[C] >> 7);
					r[B] = (r[B] << 1) | (r[B] >> 7);
					r[A] |= r[B];
					r[A] |= r[C];
					mem[0x40a8] = r[A];
					r4269();
					rp[IX] = 0x4098;
					r4332();
					mem[0x40a5] = r[L]; mem[0x40a6] = r[H];
				case 0x4328:
					rp[HL] = 0x40ab;
					mem[rp[HL]] = r[A];
					r4271();
					r441f();
					return;
			}
		}
	}

	function r40b5() {
		/*
		Inputs: ['H', 'L']
		Outputs: ['D', 'E', 'H', 'C', 'L']
		Overwrites: ['D', 'cFlag', 'H', 'L', 'E', 'B', 'C']
		*/
		r[E] = mem[rp[HL]];
		rp[HL]++;
		r[D] = mem[rp[HL]];
		rp[HL]++;
		tmp = rp[DE]; rp[DE] = rp[HL]; rp[HL] = tmp;

		// rp[BC] = 0xee43; // SMC
		r[C] = mem[0x40bb]; r[B] = mem[0x40bc];

		rp[HL] += rp[BC];
		tmp = rp[DE]; rp[DE] = rp[HL]; rp[HL] = tmp;
		return;
	}

	function r40ba() {
		/*
		Inputs: ['D', 'H', 'E', 'L']
		Outputs: ['D', 'E', 'H', 'C', 'L']
		Overwrites: ['D', 'cFlag', 'H', 'L', 'E', 'B', 'C']
		*/

		// rp[BC] = 0xee43; // SMC
		r[C] = mem[0x40bb]; r[B] = mem[0x40bc];

		rp[HL] += rp[BC];
		tmp = rp[DE]; rp[DE] = rp[HL]; rp[HL] = tmp;
		return;
	}

	function r40af() {
		/*
		Inputs: ['A', 'B', 'H', 'C', 'L']
		Outputs: ['H', 'L']
		Overwrites: ['pvFlag', 'cFlag', 'zFlag', 'sFlag', 'H', 'L']
		*/
		while (true) {
			zFlag = (r[A] == mem[rp[HL]]);
			if (zFlag) return;
			rp[HL] += rp[BC];
		}
	}

	function r441f() {
		/*
		Inputs: ['A']
		Outputs: []
		Overwrites: ['cFlag', 'zFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'B', 'C']
		*/
		rp[HL] = 0x40ae;
		r[A] = 0x00;
		zFlag = (r[A] | mem[rp[HL]]) === 0;
		r[A] = 0x0d;
		if (zFlag) {
			r[A] -= 0x03;
			rp[HL]--;
			rp[HL]--;
			rp[HL]--;
		}
		r[C] = 0xfd;
		while (true) {
			r[B] = 0xff;
			out(rp[BC], r[A]);
			r[B] = 0xbf;
			out(rp[BC], mem[rp[HL]]); rp[HL]--;
			r[A]--; sFlag = !!(r[A] & 0x80);
			if (sFlag) return;
		}
	}

	function r4139() {
		/*
		Inputs: ['IXL', 'IXH']
		Outputs: ['sFlag']
		Overwrites: ['sFlag', 'A', 'zFlag', 'pvFlag']
		*/
		tmp = (rp[IX] + 0x02) & 0xffff; mem[tmp]--; sFlag = !!(mem[tmp] & 0x80);
		if (!sFlag) return;
		r[A] = mem[(rp[IX] - 0x01) & 0xffff];
		mem[(rp[IX] + 0x02) & 0xffff] = r[A];
		return;
	}

	function r40f8() {
		/*
		Inputs: []
		Outputs: ['C']
		Overwrites: ['D', 'cFlag', 'zFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'E', 'B', 'C']
		*/
		r[A] = mem[0x40a0];
		r[C] = r[A];
		rp[HL] = 0x407a;
		cFlag = (r[A] < mem[rp[HL]]);
		if (!cFlag) {
			r[A] = 0x00;
			r[C] = r[A];
		}
		r[A]++;
		mem[0x40a0] = r[A];
		r[L] = r[C];
		r[H] = 0x00;
		rp[HL] += rp[HL];
		r[E] = mem[0x4070]; r[D] = mem[0x4071];
		rp[HL] += rp[DE];
		r[C] = mem[rp[HL]];
		rp[HL]++;
		r[A] = mem[rp[HL]];
		mem[0x4344] = r[A];
		r[A] = r[C];
		r[L] = mem[0x4074]; r[H] = mem[0x4075];
		rp[BC] = 0x0007;
		r40af();
		rp[HL]++;
		r40b5();
		mem[0x407b] = r[E]; mem[0x407c] = r[D];
		r40b5();
		mem[0x407d] = r[E]; mem[0x407e] = r[D];
		r40b5();
		mem[0x407f] = r[E]; mem[0x4080] = r[D];
	}

	function r4198() {
		/*
		Inputs: ['IXL', 'IXH', 'H', 'L']
		Outputs: ['H', 'C', 'cFlag', 'L']
		Overwrites: ['zFlag', 'cFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'B', 'C']
		*/
		var pc = 0x4198;
		while (true) {
			switch (pc) {
				case 0x4198:
					r[A] = mem[rp[HL]];
					cFlag = (r[A] < 0x60);
					if (cFlag) {pc = 0x41c6; break;}
					cFlag = (r[A] < 0x70);
					if (cFlag) {pc = 0x41d3; break;}
					zFlag = (r[A] == 0x80); cFlag = (r[A] < 0x80);
					if (cFlag) {pc = 0x41f4; break;}
					if (zFlag) {pc = 0x41eb; break;}
					zFlag = (r[A] == 0x81); cFlag = (r[A] < 0x81);
					if (zFlag) {pc = 0x41d1; break;}
					zFlag = (r[A] == 0x82);
					if (zFlag) {pc = 0x41f1; break;}
					cFlag = (r[A] < 0x8f);
					if (cFlag) {pc = 0x4210; break;}
					r[A] -= 0xa1;
					mem[(rp[IX] + 0x02) & 0xffff] = r[A];
					mem[(rp[IX] - 0x01) & 0xffff] = r[A];
					rp[HL]++;
					pc = 0x4198; break;
				case 0x41c6:
					mem[(rp[IX] + 0x01) & 0xffff] = r[A];
					mem[(rp[IX] + 0x00) & 0xffff] = 0x00;
					mem[(rp[IX] + 0x07) & 0xffff] = 0x20;
				case 0x41d1:
					rp[HL]++;
					return;
				case 0x41d3:
					r[A] -= 0x60;
					rp[SP]--; mem[rp[SP]] = r[H]; rp[SP]--; mem[rp[SP]] = r[L];
					rp[BC] = 0x0063;
					r[L] = mem[0x4076]; r[H] = mem[0x4077];
					r40af();
					rp[HL]++;
					mem[(rp[IX] + 0x03) & 0xffff] = r[L];
					mem[(rp[IX] + 0x04) & 0xffff] = r[H];
					r[L] = mem[rp[SP]]; rp[SP]++; r[H] = mem[rp[SP]]; rp[SP]++;
					rp[HL]++;
					pc = 0x4198; break;
				case 0x41eb:
					rp[HL]++;
				case 0x41ec:
					mem[(rp[IX] + 0x07) & 0xffff] = 0xff;
					return;
				case 0x41f1:
					r[A] = 0x00;
					pc = 0x41f6; break;
				case 0x41f4:
					r[A] -= 0x70;
				case 0x41f6:
					rp[SP]--; mem[rp[SP]] = r[H]; rp[SP]--; mem[rp[SP]] = r[L];
					rp[BC] = 0x0021;
					r[L] = mem[0x4072]; r[H] = mem[0x4073];
					r40af();
					rp[HL]++;
					mem[(rp[IX] + 0x05) & 0xffff] = r[L];
					mem[(rp[IX] + 0x06) & 0xffff] = r[H];
					mem[(rp[IX] - 0x02) & 0xffff] = 0x00;
					r[L] = mem[rp[SP]]; rp[SP]++; r[H] = mem[rp[SP]]; rp[SP]++;
					rp[HL]++;
					pc = 0x4198; break;
				case 0x4210:
					r[A] -= 0x80;
					mem[0x40ae] = r[A];
					rp[HL]++;
					r[A] = mem[rp[HL]];
					rp[HL]++;
					mem[0x40ac] = r[A];
					mem[(rp[IX] - 0x02) & 0xffff] = 0x01;
					rp[SP]--; mem[rp[SP]] = r[H]; rp[SP]--; mem[rp[SP]] = r[L];
					r[A] = 0x00;
					rp[BC] = 0x0021;
					r[L] = mem[0x4072]; r[H] = mem[0x4073];
					r40af();
					rp[HL]++;
					mem[(rp[IX] + 0x05) & 0xffff] = r[L];
					mem[(rp[IX] + 0x06) & 0xffff] = r[H];
					r[L] = mem[rp[SP]]; rp[SP]++; r[H] = mem[rp[SP]]; rp[SP]++;
					pc = 0x4198; break;
			}
		}
	}

	function r4235() {
		/*
		Inputs: ['IXL', 'cFlag', 'IXH']
		Outputs: ['H', 'C', 'cFlag', 'L']
		Overwrites: ['D', 'zFlag', 'cFlag', 'sFlag', 'H', 'L', 'A', 'pvFlag', 'E', 'C']
		*/
		var pc = 0x4235;
		while (true) {
			switch (pc) {
				case 0x41ec:
					mem[(rp[IX] + 0x07) & 0xffff] = 0xff;
					return;
				case 0x4235:
					r[A] = mem[(rp[IX] + 0x07) & 0xffff];
					r[A]++; zFlag = (r[A] === 0x00);
					if (zFlag) return;
					r[A]--;
					r[A]--; zFlag = (r[A] === 0x00); sFlag = !!(r[A] & 0x80); pvFlag = ((r[A] & 0x7f) == 0x7f);
					mem[(rp[IX] + 0x07) & 0xffff] = r[A];
					tmp = (sFlag << 7) | (zFlag << 6) | (pvFlag << 2) | cFlag; rp[SP]--; mem[rp[SP]] = r[A]; rp[SP]--; mem[rp[SP]] = tmp;
					r[A] = mem[(rp[IX] + 0x00) & 0xffff];
					r[C] = r[A];
					r[A]++;
					r[A] &= 0x1f;
					mem[(rp[IX] + 0x00) & 0xffff] = r[A];
					tmp = mem[rp[SP]]; rp[SP] += 2; cFlag = !!(tmp & 0x01); zFlag = !!(tmp & 0x40);
					if (!zFlag) return;
					r[E] = mem[(rp[IX] + 0x03) & 0xffff];
					r[D] = mem[(rp[IX] + 0x04) & 0xffff];
					rp[HL] = 0x0060;
					tmp = rp[HL] + rp[DE]; rp[HL] = tmp; cFlag = (tmp >= 0x10000);
					r[A] = mem[rp[HL]];
					r[A]--; sFlag = !!(r[A] & 0x80);
					if (sFlag) {pc = 0x41ec; break;}
					r[C] = r[A];
					r[A]++;
					r[A] &= 0x1f; cFlag = false;
					mem[(rp[IX] + 0x00) & 0xffff] = r[A];
					rp[HL]++;
					r[A] = mem[rp[HL]];
					r[A]++;
					mem[(rp[IX] + 0x07) & 0xffff] = r[A];
					return;
			}
		}
	}

	function r40c0() {
		/*
		Inputs: ['A', 'IXL', 'IXH']
		Outputs: ['D', 'H', 'IXL', 'L', 'E', 'B', 'C', 'IXH']
		Overwrites: ['D', 'cFlag', 'zFlag', 'sFlag', 'IXL', 'H', 'L', 'E', 'A', 'pvFlag', 'B', 'C', 'IXH']
		*/
		r[D] = 0x00;
		r[E] = r[A];
		r[A] += r[A];
		r[A] += r[E];
		r[E] = r[A];
		rp[IX] += rp[DE];
		r[A] = mem[(rp[IX] + 0x01) & 0xffff];
		zFlag = !(r[A] & 0x80);
		r[C] = 0x10;
		if (zFlag) {
			r[C] = r[D];
		}
		zFlag = !(r[A] & 0x40);
		r[B] = 0x02;
		if (zFlag) {
			r[B] = r[D];
		}
		r[A] &= 0x1f;
		r[H] = r[A];
		r[E] = mem[(rp[IX] + 0x02) & 0xffff];
		r[A] = mem[(rp[IX] + 0x00) & 0xffff];
		tmp = (sFlag << 7) | (zFlag << 6) | (pvFlag << 2) | cFlag; rp[SP]--; mem[rp[SP]] = r[A]; rp[SP]--; mem[rp[SP]] = tmp;
		r[A] &= 0xf0;
		r[A] = (r[A] >> 1) | (r[A] << 7);
		r[A] = (r[A] >> 1) | (r[A] << 7);
		r[A] = (r[A] >> 1) | (r[A] << 7);
		r[A] = (r[A] >> 1) | (r[A] << 7);
		r[D] = r[A];
		rp[SP]++; r[A] = mem[rp[SP]]; rp[SP]++;
		r[A] &= 0x0f;
		r[L] = r[A];
		zFlag = !(mem[(rp[IX] + 0x01) & 0xffff] & 0x20);
		if (zFlag) return;
		r[D] |= 0x10;
	}

	function r4269() {
		/*
		Apply noise values to AY registers. If C (noise mask) is zero, write H (noise value) to AY reg 6.

		Inputs: ['H', 'C']
		Outputs: ['pvFlag', 'zFlag', 'cFlag', 'sFlag']
		Overwrites: ['A', 'pvFlag', 'cFlag', 'zFlag', 'sFlag']
		*/
		r[A] = r[C];
		zFlag = (r[A] === 0); cFlag = false; sFlag = !!(r[A] & 0x80);
		if (!zFlag) return;
		r[A] = r[H];
		mem[0x40a7] = r[A];
		return;
	}

	function r4332() {
		/*
		Inputs: ['D', 'cFlag', 'zFlag', 'sFlag', 'IXL', 'L', 'E', 'pvFlag', 'IXH']
		Outputs: ['A', 'H', 'cFlag', 'L']
		Overwrites: ['D', 'cFlag', 'zFlag', 'sFlag', 'H', 'L', 'A', 'E', 'pvFlag']
		*/
		r[A] = r[L];
		tmp = (sFlag << 7) | (zFlag << 6) | (pvFlag << 2) | cFlag; rp[SP]--; mem[rp[SP]] = r[A]; rp[SP]--; mem[rp[SP]] = tmp;
		rp[SP]--; mem[rp[SP]] = r[D]; rp[SP]--; mem[rp[SP]] = r[E];
		r[L] = mem[(rp[IX] + 0x05) & 0xffff];
		r[H] = mem[(rp[IX] + 0x06) & 0xffff];

		// rp[DE] = 0x000a; // SMC
		r[E] = mem[0x433c]; r[D] = mem[0x433d];

		rp[HL] += rp[DE];
		r[A] = mem[(rp[IX] + 0x01) & 0xffff];
		r[A] += mem[rp[HL]];

		// r[A] += 0x00; // SMC
		r[A] += mem[0x4344];

		r[A] += r[A];
		r[E] = r[A];
		r[D] = 0x00;
		rp[HL] = 0x435f;
		rp[HL] += rp[DE];
		r[E] = mem[rp[HL]];
		rp[HL]++;
		r[D] = mem[rp[HL]];
		rp[HL] = rp[DE];
		r[E] = mem[rp[SP]]; rp[SP]++; r[D] = mem[rp[SP]]; rp[SP]++;
		rp[SP]++; r[A] = mem[rp[SP]]; rp[SP]++;
		zFlag = !(r[D] & 0x10);
		if (!zFlag) {
			r[D] &= 0xef;
			tmp = rp[HL] + rp[DE]; rp[HL] = tmp; cFlag = (tmp >= 0x10000);
		} else {
			cFlag = false;
			tmp = rp[HL] - rp[DE] - cFlag; rp[HL] = tmp; cFlag = (tmp < 0);
		}
	}

	function r4271() {
		/*
		Inputs: ['IXL', 'IXH', 'H', 'L']
		Outputs: ['A', 'cFlag']
		Overwrites: ['zFlag', 'cFlag', 'sFlag', 'A', 'pvFlag']
		*/
		r[A] = mem[(rp[IX] + 0x07) & 0xffff];
		r[A]++; zFlag = (r[A] === 0x00);
		if (zFlag) return;
		r[A] = mem[(rp[IX] - 0x02) & 0xffff];
		zFlag = (r[A] === 0); cFlag = false;
		if (zFlag) return;
		zFlag = (r[A] == 0x02); cFlag = (r[A] < 0x02);
		if (!zFlag) {
			mem[(rp[IX] - 0x02) & 0xffff] = 0x02;
		} else {
			r[A] = 0x00; cFlag = false;
			mem[0x40ae] = r[A];
		}
		mem[rp[HL]] |= 0x10;
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
