# 지정한 슬라이드만 MP4로 내보낸다 (애니메이션 검수용, Windows + PowerPoint 필요). 원본은 건드리지 않는다.
# 사용: powershell -ExecutionPolicy Bypass -File export_video.ps1 -Pptx deck.pptx -Slides "4,10" -Out check.mp4 [-SlideSeconds 7]
# 검수: ffmpeg -i check.mp4 -vf fps=2 f_%02d.png 로 프레임을 뽑아 순서대로 본다.
param([Parameter(Mandatory)][string]$Pptx, [Parameter(Mandatory)][string]$Slides,
      [Parameter(Mandatory)][string]$Out, [int]$SlideSeconds = 7, [int]$Height = 540)
$ErrorActionPreference = 'Stop'
# "4,10,17" 문자열로 받는다 — powershell -File 로 넘긴 int[]는 한 덩어리 문자열이 되어 전부 삭제되는 문제가 있었다
$keep = $Slides -split '[,\s]+' | Where-Object { $_ } | ForEach-Object { [int]$_ }
if (-not $keep) { throw "슬라이드 번호가 없습니다: '$Slides'" }
$tmp = Join-Path $env:TEMP ("kosoe_vid_" + [guid]::NewGuid().ToString('N') + '.pptx')
Copy-Item (Resolve-Path $Pptx).Path $tmp
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($tmp, $false, $false, $false)
try {
  for ($i = $pres.Slides.Count; $i -ge 1; $i--) { if ($keep -notcontains $i) { $pres.Slides.Item($i).Delete() } }
  if ($pres.Slides.Count -eq 0) { throw '남은 슬라이드가 없습니다' }
  foreach ($s in $pres.Slides) { $s.SlideShowTransition.AdvanceOnTime = -1; $s.SlideShowTransition.AdvanceTime = $SlideSeconds }
  $outPath = [IO.Path]::GetFullPath($Out)
  $pres.CreateVideo($outPath, $true, $SlideSeconds, $Height, 15, 85)
  $t0 = Get-Date   # 상태: 1 대기, 2 진행, 3 완료, 4 실패 (시작 직후 0일 수 있음)
  while ($pres.CreateVideoStatus -ne 3 -and $pres.CreateVideoStatus -ne 4 -and ((Get-Date) - $t0).TotalSeconds -lt 900) { Start-Sleep -Milliseconds 500 }
  if ($pres.CreateVideoStatus -ne 3) { throw "동영상 내보내기 실패 (status $($pres.CreateVideoStatus))" }
  "ok $($pres.Slides.Count) slides -> $outPath"
} finally { $pres.Close(); $app.Quit(); Remove-Item $tmp -ErrorAction SilentlyContinue }
