#!/bin/sh

rm -f output/ref.log output/alan.log
for f in testfiles/*.stc
do
	echo $f >> output/ref.log
	node z80ref/run.js $f >> output/ref.log
	echo $f >> output/alan.log
	node stc_player.js $f >> output/alan.log
done
diff -u output/ref.log output/alan.log
