z80module = require('./z80');

var Z80Processor = z80module.buildZ80();

var _mem = new Uint8Array(0x10000);

/* load STC player at address 0x4000 */
var STCPlayerBin = new Uint8Array([33,60,68,195,9,64,195,68,65,243,126,50,120,64,34,187,64,35,205,181,64,26,19,60,50,122,64,237,83,112,64,205,181,64,237,83,114,64,213,205,181,64,237,83,116,64,33,27,0,205,186,64,235,34,118,64,33,129,64,34,123,64,33,130,64,17,131,64,1,44,0,112,237,176,225,1,33,0,175,205,175,64,61,50,139,64,50,149,64,50,159,64,62,1,50,121,64,35,34,137,64,34,147,64,34,157,64,205,31,68,251,201,119,241,143,241,19,242,94,238,6,1,12,69,231,184,105,87,106,255,0,0,0,0,0,0,0,144,241,255,0,0,0,0,0,0,0,144,241,255,0,0,0,0,0,0,0,144,241,255,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,190,200,9,195,175,64,94,35,86,35,235,1,67,238,9,235,201,22,0,95,135,131,95,221,25,221,126,1,203,127,14,16,194,211,64,74,203,119,6,2,194,219,64,66,230,31,103,221,94,2,221,126,0,245,230,240,15,15,15,15,87,241,230,15,111,221,203,1,110,200,203,226,201,58,160,64,79,33,122,64,190,218,5,65,175,79,60,50,160,64,105,38,0,41,237,91,112,64,25,78,35,126,50,68,67,121,42,116,64,1,7,0,205,175,64,35,205,181,64,237,83,123,64,205,181,64,237,83,125,64,205,181,64,237,83,127,64,201,221,53,2,240,221,126,255,221,119,2,201,58,121,64,61,50,121,64,194,142,66,58,120,64,50,121,64,221,33,132,64,205,57,65,242,111,65,42,123,64,126,60,204,248,64,42,123,64,205,152,65,34,123,64,221,33,142,64,205,57,65,242,130,65,42,125,64,205,152,65,34,125,64,221,33,152,64,205,57,65,242,142,66,42,127,64,205,152,65,34,127,64,195,142,66,126,254,96,218,198,65,254,112,218,211,65,254,128,218,244,65,202,235,65,254,129,202,209,65,254,130,202,241,65,254,143,218,16,66,214,161,221,119,2,221,119,255,35,195,152,65,221,119,1,221,54,0,0,221,54,7,32,35,201,214,96,229,1,99,0,42,118,64,205,175,64,35,221,117,3,221,116,4,225,35,195,152,65,35,221,54,7,255,201,175,24,2,214,112,229,1,33,0,42,114,64,205,175,64,35,221,117,5,221,116,6,221,54,254,0,225,35,195,152,65,214,128,50,174,64,35,126,35,50,172,64,221,54,254,1,229,175,1,33,0,42,114,64,205,175,64,35,221,117,5,221,116,6,225,195,152,65,221,126,7,60,200,61,61,221,119,7,245,221,126,0,79,60,230,31,221,119,0,241,192,221,94,3,221,86,4,33,96,0,25,126,61,250,236,65,79,60,230,31,221,119,0,35,126,60,221,119,7,201,121,183,192,124,50,167,64,201,221,126,7,60,200,221,126,254,183,200,254,2,202,135,66,221,54,254,2,195,139,66,175,50,174,64,203,230,201,221,33,132,64,205,53,66,121,50,60,67,221,42,135,64,205,192,64,121,176,15,50,168,64,221,33,132,64,221,126,7,60,202,186,66,205,105,66,205,50,67,34,161,64,33,169,64,119,205,113,66,221,33,142,64,205,53,66,221,126,7,60,202,239,66,121,50,60,67,221,42,145,64,205,192,64,58,168,64,177,176,50,168,64,205,105,66,221,33,142,64,205,50,67,34,163,64,33,170,64,119,205,113,66,221,33,152,64,205,53,66,221,126,7,60,202,40,67,121,50,60,67,221,42,155,64,205,192,64,58,168,64,203,1,203,0,176,177,50,168,64,205,105,66,221,33,152,64,205,50,67,34,165,64,33,171,64,119,205,113,66,195,31,68,125,245,213,221,110,5,221,102,6,17,10,0,25,221,126,1,134,198,0,135,95,22,0,33,95,67,25,94,35,86,235,209,241,203,98,40,4,203,162,25,201,167,237,82,201,248,14,16,14,96,13,128,12,216,11,40,11,136,10,240,9,96,9,224,8,88,8,224,7,124,7,8,7,176,6,64,6,236,5,148,5,68,5,248,4,176,4,112,4,44,4,240,3,190,3,132,3,88,3,32,3,246,2,202,2,162,2,124,2,88,2,56,2,22,2,248,1,223,1,194,1,172,1,144,1,123,1,101,1,81,1,62,1,44,1,28,1,11,1,252,0,239,0,225,0,214,0,200,0,189,0,178,0,168,0,159,0,150,0,142,0,133,0,126,0,119,0,112,0,107,0,100,0,94,0,89,0,84,0,79,0,75,0,71,0,66,0,63,0,59,0,56,0,53,0,50,0,47,0,44,0,42,0,39,0,37,0,35,0,33,0,31,0,29,0,28,0,26,0,25,0,23,0,22,0,21,0,19,0,18,0,17,0,16,0,15,0,33,174,64,175,182,62,13,32,5,214,3,43,43,43,14,253,6,255,237,121,6,191,237,171,61,242,47,68,201]);
for (var i = 0; i < STCPlayerBin.length; i++) {
	_mem[0x4000 + i] = STCPlayerBin[i];
}

var ayRegisters = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false];
var selectedAYRegister = 0;

var z80 = Z80Processor({
	memory: {
		'read': function(addr) {return _mem[addr];},
		'write': function(addr, val) {_mem[addr] = val;}
	},
	ioBus: {
		'write': function(addr, val) {
			if ((addr & 0xc002) == 0xc000) {
				/* AY register select */
				selectedAYRegister = val;
			} else if ((addr & 0xc002) == 0x8000) {
				/* AY register write */
				ayRegisters[selectedAYRegister] = val;
				if (selectedAYRegister == 13) ayRegisters[14] = true;
			}
		}
	}
});

var fs = require('fs');
fs.readFile(process.argv[2], function(err, stc) {
	/* load STC data at address 0x443c */
	for (i = 0; i < stc.length; i++) {
		_mem[0x443c + i] = stc[i];
	}

	/* init player */
	var count = z80.runRoutine(0x4000, 0x3f00);

	for (var frame = 0; frame < 100000; frame++) {
		ayRegisters[14] = false;
		count = z80.runRoutine(0x4006, 0x3f00);
		console.log(ayRegisters.slice());
	}
});
