# 타임라인 JSON대로 PowerPoint 애니메이션을 추가한다 (Windows + PowerPoint 필요). 파일을 직접 저장한다.
# 사용: powershell -ExecutionPolicy Bypass -File animate.ps1 -Pptx deck.pptx -Timeline timeline.json
#
# timeline.json = 순서대로 실행될 효과 목록:
# [{ "slide":4, "shape":"Kosoe Layer bridge_kosoe", "fx":"fade|wipe|appear|path|teeter",
#    "trigger":"after|with|click", "dur":1.0, "delay":0, "dir":"left|right|up|down",
#    "path":"M -0.139 0 L 0 0 E", "linear":true }, ...]
# - shape: 도형 이름. 그룹이면 그룹 이름(예: 메인 그림이 든 'Group 10')
# - path : 슬라이드 폭/높이 기준 비율 좌표. 도형은 '도착 위치'에 두고 시작점을 음수로 준다
#          (예: 원본 405px 왼쪽에서 출발 → place_layers.py가 알려 준 path unit × -405)
# - 등장(fade/wipe) 직후 같은 도형에 path를 "with"로 붙이면 '나타나며 이동'이 된다
param([Parameter(Mandatory)][string]$Pptx, [Parameter(Mandatory)][string]$Timeline)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName 'Microsoft.Office.Interop.PowerPoint'
$E = [Microsoft.Office.Interop.PowerPoint.MsoAnimEffect]
$fxMap = @{ fade = $E::msoAnimEffectFade; wipe = $E::msoAnimEffectWipe; appear = $E::msoAnimEffectAppear
            path = $E::msoAnimEffectPathRight; teeter = $E::msoAnimEffectTeeter }
$dirMap = @{ up = 1; right = 2; down = 3; left = 4 }    # msoAnimDirection
$trigMap = @{ click = 1; with = 2; after = 3 }          # msoAnimTrigger

$steps = Get-Content -Raw -Encoding UTF8 $Timeline | ConvertFrom-Json
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open((Resolve-Path $Pptx).Path, $false, $false, $false)
try {
  foreach ($st in $steps) {
    $slide = $pres.Slides.Item([int]$st.slide)
    $shape = $slide.Shapes.Item([string]$st.shape)
    $trigger = if ($st.trigger) { $trigMap[[string]$st.trigger] } else { 3 }
    $eff = $slide.TimeLine.MainSequence.AddEffect($shape, $fxMap[[string]$st.fx], 0, $trigger)
    if ($st.dur) { $eff.Timing.Duration = [double]$st.dur }
    if ($st.delay) { $eff.Timing.TriggerDelayTime = [double]$st.delay }
    if ($st.dir) { $eff.EffectParameters.Direction = $dirMap[[string]$st.dir] }
    if ($st.fx -eq 'path') {
      $eff.Behaviors.Item(1).MotionEffect.Path = [string]$st.path
      if ($st.linear) { $eff.Timing.SmoothStart = 0; $eff.Timing.SmoothEnd = 0 }
    }
    "slide $($st.slide): $($st.fx) '$($st.shape)' ($($st.trigger))"
  }
  $pres.Save()
} finally { $pres.Close(); $app.Quit() }
