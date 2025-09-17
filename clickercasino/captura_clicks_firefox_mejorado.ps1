
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Windows.Forms;
    using System.Drawing;
    using System.Text;
    using System.Diagnostics;
    
    public class FirefoxMouseHook {
        private const int WH_MOUSE_LL = 14;
        private const int WM_LBUTTONDOWN = 0x0201;
        
        public delegate IntPtr LowLevelMouseProc(int nCode, IntPtr wParam, IntPtr lParam);
        public static LowLevelMouseProc _proc = HookCallback;
        public static IntPtr _hookID = IntPtr.Zero;
        
        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern IntPtr SetWindowsHookEx(int idHook, LowLevelMouseProc lpfn, IntPtr hMod, uint dwThreadId);
        
        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool UnhookWindowsHookEx(IntPtr hhk);
        
        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
        
        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);
        
        [DllImport("user32.dll")]
        public static extern IntPtr WindowFromPoint(System.Drawing.Point pt);
        
        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
        
        [DllImport("user32.dll")]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
        
        [StructLayout(LayoutKind.Sequential)]
        public struct POINT {
            public int x;
            public int y;
        }
        
        [StructLayout(LayoutKind.Sequential)]
        public struct MSLLHOOKSTRUCT {
            public POINT pt;
            public uint mouseData;
            public uint flags;
            public uint time;
            public IntPtr dwExtraInfo;
        }
        
        public static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam) {
            if (nCode >= 0 && wParam == (IntPtr)WM_LBUTTONDOWN) {
                MSLLHOOKSTRUCT hookStruct = (MSLLHOOKSTRUCT)Marshal.PtrToStructure(lParam, typeof(MSLLHOOKSTRUCT));
                
                // Verificar si el click está dentro de la ventana Firefox
                System.Drawing.Point clickPoint = new System.Drawing.Point(hookStruct.pt.x, hookStruct.pt.y);
                IntPtr windowHandle = WindowFromPoint(clickPoint);
                StringBuilder windowTitle = new StringBuilder(256);
                GetWindowText(windowHandle, windowTitle, 256);
                
                // Obtener información del proceso
                uint processId;
                GetWindowThreadProcessId(windowHandle, out processId);
                
                try {
                    Process process = Process.GetProcessById((int)processId);
                    string processName = process.ProcessName.ToLower();
                    string title = windowTitle.ToString().ToLower();
                    
                    // Detección mejorada para Firefox
                    bool esFirefox = processName.Contains("firefox") || 
                                   title.Contains("firefox") || 
                                   title.Contains("mozilla") ||
                                   processName.Contains("gecko") ||
                                   title.Contains("lightning roulette") ||
                                   title.Contains("evolution");
                    
                    if (esFirefox) {
                        // Verificar que está dentro del área de la ventana Firefox detectada
                        int ventanaX = -7;
                        int ventanaY = -7;
                        int ventanaWidth = 1550;
                        int ventanaHeight = 830;
                        
                        if (hookStruct.pt.x >= ventanaX && hookStruct.pt.x <= ventanaX + ventanaWidth &&
                            hookStruct.pt.y >= ventanaY && hookStruct.pt.y <= ventanaY + ventanaHeight) {
                            
                            Console.WriteLine("FIREFOX_CLICK_CAPTURED:" + hookStruct.pt.x + "," + hookStruct.pt.y + "," + DateTime.Now.Ticks + "," + processName + "," + title);
                        }
                    }
                } catch {
                    // Fallback a detección por título si no se puede obtener el proceso
                    string title = windowTitle.ToString().ToLower();
                    if (title.Contains("firefox") || title.Contains("mozilla") || title.Contains("lightning") || title.Contains("roulette")) {
                        Console.WriteLine("FIREFOX_CLICK_CAPTURED:" + hookStruct.pt.x + "," + hookStruct.pt.y + "," + DateTime.Now.Ticks + ",fallback," + title);
                    }
                }
            }
            return CallNextHookEx(_hookID, nCode, wParam, lParam);
        }
        
        public static void StartHook() {
            _hookID = SetWindowsHookEx(WH_MOUSE_LL, _proc, GetModuleHandle("user32"), 0);
            if (_hookID == IntPtr.Zero) {
                Console.WriteLine("ERROR_HOOK_FAILED");
                return;
            }
            Console.WriteLine("HOOK_STARTED_SUCCESSFULLY");
            Application.Run();
        }
        
        public static void StopHook() {
            UnhookWindowsHookEx(_hookID);
        }
    }
"@

# Iniciar captura en background
$job = Start-Job -ScriptBlock {
    try {
        [FirefoxMouseHook]::StartHook()
    } catch {
        Write-Host "ERROR_STARTING_HOOK: $($_.Exception.Message)"
    }
}

# Esperar señal de terminación (archivo temporal)
while (-not (Test-Path "stop_firefox_capture.tmp")) {
    Start-Sleep -Milliseconds 100
}

# Detener captura
Stop-Job $job
Remove-Job $job
if (Test-Path "stop_firefox_capture.tmp") {
    Remove-Item "stop_firefox_capture.tmp" -Force
}
