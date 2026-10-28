# Özgün 3D ajanlar (Blender)

Eksik Parçalar sekmesindeki ajanlar için gerçekçi, **özgün** modeller ve döner render.

- Beden: [MakeHuman](http://www.makehumancommunity.org) temel modeli ve iskeleti — **CC0** (kısıtlamasız).
  `makehuman/data/3dobjs/base.obj`, `makehuman/data/rigs/default.mhskel`, `default_weights.mhw`.
- Kıyafet ve teçhizat: bu klasördeki kodla üretilir (oyun dosyası, modeli ya da dokusu kullanılmaz).

```
python mh_pose.py <makehuman/data> posed.json                 # bedeni poza sok (tüfek iki elde)
blender-python build_mh.py -- --pose posed.json --outfit operator --views front,q3,side,back --out out/
blender-python build_mh.py -- --pose posed.json --outfit operator --turntable 48 --out out/   # 360° + yuva maskeleri
```
`blender-python`: `pip install bpy` (Blender 5.x, Python 3.11).
