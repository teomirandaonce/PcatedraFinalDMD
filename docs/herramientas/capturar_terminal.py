"""
Ejecuta un comando, guarda su salida real y la renderiza como captura PNG
con estilo de terminal (Google Chrome en modo headless).

Uso: python docs/herramientas/capturar_terminal.py salida.png "titulo" "comando"
"""
import html
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    salida_png, titulo, comando = sys.argv[1], sys.argv[2], sys.argv[3]
    r = subprocess.run(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    texto = r.stdout.rstrip()
    lineas = texto.splitlines() or [""]
    ancho_chars = max(80, max(len(l) for l in lineas) + 2, len(comando) + 30)
    ancho = min(1600, int(ancho_chars * 8.2) + 40)
    alto = (len(lineas) + 2) * 18 + 70
    pagina = f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0;background:#1e1e1e}}
.bar{{height:28px;background:#3a3a3c;display:flex;align-items:center;padding-left:12px;gap:8px;
 font:13px -apple-system,sans-serif;color:#ccc}}
.d{{width:12px;height:12px;border-radius:50%}}
.t{{flex:1;text-align:center;margin-right:60px}}
pre{{margin:0;padding:10px 14px;color:#e6e6e6;font:13.5px/18px Menlo,monospace;white-space:pre}}
.p{{color:#5fd75f}} .c{{color:#fff;font-weight:bold}}
</style><div class="bar"><span class="d" style="background:#ff5f57"></span><span class="d" style="background:#febc2e">
</span><span class="d" style="background:#28c840"></span><span class="t">{html.escape(titulo)}</span></div>
<pre><span class="p">PcatedraFinalDMD $</span> <span class="c">{html.escape(comando)}</span>
{html.escape(texto)}</pre>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(pagina)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={Path(salida_png).resolve()}",
                    f"--window-size={ancho},{alto}", f"file://{f.name}"],
                   capture_output=True, check=True)
    print(texto)
    print(f"--> {salida_png} (exit={r.returncode})")


if __name__ == "__main__":
    main()
