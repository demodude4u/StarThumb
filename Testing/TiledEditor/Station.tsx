<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.10.1" name="Station" tilewidth="16" tileheight="16" tilecount="128" columns="8">
 <image source="StationTiles.png" trans="ff00ff" width="128" height="256"/>
 <tile id="4" probability="0.01"/>
 <tile id="5" probability="0.01"/>
 <tile id="6" probability="0.01"/>
 <tile id="7" probability="0.01"/>
 <tile id="12" probability="0.01"/>
 <tile id="13" probability="0.01"/>
 <tile id="14" probability="0.01"/>
 <tile id="15" probability="0.01"/>
 <tile id="20" probability="0.01"/>
 <tile id="21" probability="0.01"/>
 <tile id="22" probability="0.01"/>
 <tile id="23" probability="0.01"/>
 <tile id="24" probability="0.01"/>
 <tile id="28" probability="0.01"/>
 <tile id="29" probability="0.01"/>
 <tile id="30" probability="0.01"/>
 <tile id="31" probability="0.01"/>
 <tile id="64" probability="0.1"/>
 <tile id="65" probability="0.1"/>
 <tile id="80" probability="0.1"/>
 <tile id="82" probability="0.1"/>
 <wangsets>
  <wangset name="Path" type="edge" tile="-1">
   <wangcolor name="Path" color="#ff0000" tile="-1" probability="1"/>
   <wangtile tileid="36" wangid="0,0,0,0,1,0,0,0"/>
   <wangtile tileid="37" wangid="0,0,1,0,1,0,0,0"/>
   <wangtile tileid="38" wangid="0,0,1,0,1,0,1,0"/>
   <wangtile tileid="39" wangid="0,0,0,0,1,0,1,0"/>
   <wangtile tileid="44" wangid="1,0,0,0,1,0,0,0"/>
   <wangtile tileid="45" wangid="1,0,1,0,1,0,0,0"/>
   <wangtile tileid="46" wangid="1,0,1,0,1,0,1,0"/>
   <wangtile tileid="47" wangid="1,0,0,0,1,0,1,0"/>
   <wangtile tileid="52" wangid="1,0,0,0,0,0,0,0"/>
   <wangtile tileid="53" wangid="1,0,1,0,0,0,0,0"/>
   <wangtile tileid="54" wangid="1,0,1,0,0,0,1,0"/>
   <wangtile tileid="55" wangid="1,0,0,0,0,0,1,0"/>
   <wangtile tileid="61" wangid="0,0,1,0,0,0,0,0"/>
   <wangtile tileid="62" wangid="0,0,1,0,0,0,1,0"/>
   <wangtile tileid="63" wangid="0,0,0,0,0,0,1,0"/>
  </wangset>
  <wangset name="Station" type="mixed" tile="-1">
   <wangcolor name="Exterior" color="#ff0000" tile="-1" probability="1"/>
   <wangcolor name="Path" color="#ff00d8" tile="-1" probability="1"/>
   <wangtile tileid="0" wangid="0,0,0,0,0,1,0,0"/>
   <wangtile tileid="1" wangid="0,1,0,1,0,0,0,0"/>
   <wangtile tileid="2" wangid="0,0,0,1,0,1,0,1"/>
   <wangtile tileid="3" wangid="0,0,0,1,0,1,0,0"/>
   <wangtile tileid="4" wangid="0,0,0,0,0,1,0,0"/>
   <wangtile tileid="5" wangid="0,1,0,1,0,0,0,0"/>
   <wangtile tileid="6" wangid="0,0,0,1,0,1,0,1"/>
   <wangtile tileid="7" wangid="0,0,0,0,0,1,0,0"/>
   <wangtile tileid="8" wangid="0,0,0,1,0,0,0,1"/>
   <wangtile tileid="9" wangid="0,1,0,1,0,1,0,0"/>
   <wangtile tileid="10" wangid="0,1,0,1,0,1,0,1"/>
   <wangtile tileid="11" wangid="0,1,0,0,0,1,0,1"/>
   <wangtile tileid="12" wangid="0,0,0,1,0,0,0,1"/>
   <wangtile tileid="13" wangid="0,1,0,1,0,1,0,0"/>
   <wangtile tileid="14" wangid="0,1,0,1,0,1,0,1"/>
   <wangtile tileid="15" wangid="0,0,0,0,0,1,0,1"/>
   <wangtile tileid="16" wangid="0,1,0,0,0,0,0,0"/>
   <wangtile tileid="17" wangid="0,1,0,0,0,0,0,1"/>
   <wangtile tileid="18" wangid="0,1,0,1,0,0,0,1"/>
   <wangtile tileid="19" wangid="0,0,0,0,0,1,0,1"/>
   <wangtile tileid="20" wangid="0,1,0,0,0,0,0,0"/>
   <wangtile tileid="21" wangid="0,1,0,0,0,0,0,1"/>
   <wangtile tileid="22" wangid="0,1,0,1,0,0,0,1"/>
   <wangtile tileid="23" wangid="0,0,0,0,0,1,0,1"/>
   <wangtile tileid="24" wangid="0,0,0,1,0,1,0,0"/>
   <wangtile tileid="25" wangid="0,0,0,1,0,0,0,0"/>
   <wangtile tileid="26" wangid="0,1,0,0,0,1,0,0"/>
   <wangtile tileid="27" wangid="0,0,0,0,0,0,0,1"/>
   <wangtile tileid="28" wangid="0,1,0,0,0,0,0,1"/>
   <wangtile tileid="29" wangid="0,0,0,1,0,0,0,0"/>
   <wangtile tileid="30" wangid="0,1,0,0,0,1,0,0"/>
   <wangtile tileid="31" wangid="0,0,0,0,0,0,0,1"/>
   <wangtile tileid="36" wangid="0,0,0,0,2,0,0,0"/>
   <wangtile tileid="37" wangid="0,0,2,0,2,0,0,0"/>
   <wangtile tileid="38" wangid="0,0,2,0,2,0,2,0"/>
   <wangtile tileid="39" wangid="0,0,0,0,2,0,2,0"/>
   <wangtile tileid="44" wangid="2,0,0,0,2,0,0,0"/>
   <wangtile tileid="45" wangid="2,0,2,0,2,0,0,0"/>
   <wangtile tileid="46" wangid="2,0,2,0,2,0,2,0"/>
   <wangtile tileid="47" wangid="2,0,0,0,2,0,2,0"/>
   <wangtile tileid="52" wangid="2,0,0,0,0,0,0,0"/>
   <wangtile tileid="53" wangid="2,0,2,0,0,0,0,0"/>
   <wangtile tileid="54" wangid="2,0,2,0,0,0,2,0"/>
   <wangtile tileid="55" wangid="2,0,0,0,0,0,2,0"/>
   <wangtile tileid="61" wangid="0,0,2,0,0,0,0,0"/>
   <wangtile tileid="62" wangid="0,0,2,0,0,0,2,0"/>
   <wangtile tileid="63" wangid="0,0,0,0,0,0,2,0"/>
   <wangtile tileid="64" wangid="0,1,0,1,0,0,0,0"/>
   <wangtile tileid="65" wangid="0,1,0,0,0,0,0,1"/>
   <wangtile tileid="80" wangid="0,0,0,1,0,1,0,0"/>
   <wangtile tileid="82" wangid="0,0,0,0,0,1,0,1"/>
   <wangtile tileid="92" wangid="0,1,0,0,0,0,0,1"/>
   <wangtile tileid="94" wangid="0,0,0,1,0,1,0,0"/>
  </wangset>
 </wangsets>
</tileset>
