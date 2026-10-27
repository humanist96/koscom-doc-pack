# PowerPoint로 모든 슬라이드를 PNG로 내보낸다 (Windows + PowerPoint 필요).
# 사용: powershell -ExecutionPolicy Bypass -File render.ps1 -Pptx deck.pptx -Out renders [-Width 1600]
param([Parameter(Mandatory)][string]$Pptx, [Parameter(Mandatory)][string]$Out, [int]$Width = 1600)
$ErrorActionPreference = 'Stop'
$src = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force $Out | Out-Null
$outDir = (Resolve-Path $Out).Path
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($src, $true, $false, $false)   # 읽기 전용, 창 없음
try {
  $h = [int]($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
  $i = 1
  foreach ($s in $pres.Slides) { $s.Export((Join-Path $outDir ('s{0:D2}.png' -f $i)), 'PNG', $Width, $h); $i++ }
  "rendered $($i - 1) slides -> $outDir"
} finally { $pres.Close(); $app.Quit() }
