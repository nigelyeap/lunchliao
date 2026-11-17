cd /Users/nigelyeap/Documents/lunchliao-hd/tools/blender/heroes_toy/_tmp_siao
cat partA.py partB.py partC.py partD.py > ../siao.py
cd /Users/nigelyeap/Documents/lunchliao-hd
/opt/homebrew/bin/blender -b -P tools/blender/heroes_toy/siao.py -- $@ > tools/blender/heroes_toy/_tmp_siao/log.txt 2>&1
grep -v Deprecat tools/blender/heroes_toy/_tmp_siao/log.txt | grep -v "use_nodes" | tail -${LINES_N:-25}
