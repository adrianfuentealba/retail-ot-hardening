#!/bin/sh
set -eu
mkdir -p /evidence/osquery /home/student/.vnc /home/student/Desktop /home/student/lab/downloads /var/log/osquery /evidence
chown -R student:student /home/student
printf '#!/bin/sh\nexec startxfce4\n' >/home/student/.vnc/xstartup
chmod +x /home/student/.vnc/xstartup
cat >/home/student/Desktop/Taller.desktop <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Terminal del laboratorio
Exec=xfce4-terminal
Icon=utilities-terminal
Terminal=false
EOF
cat >/home/student/Desktop/Portal.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Retail OT — Portal y guías
Exec=firefox-esr http://panel:8000
Icon=web-browser
Terminal=false
EOF
cat >/home/student/Desktop/Guias.desktop <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Guías paso a paso — Retail OT
Comment=Instrucciones locales y comandos copiables para todos los talleres
Exec=firefox-esr http://127.0.0.1:8010/guides/
Icon=help-browser
Terminal=false
EOF
printf 'GUÍAS LOCALES RETAIL OT\n\nDoble clic en Guías paso a paso, o escriba: labctl guides\nEn Firefox: Copiar. En Terminal: Ctrl+Shift+V y Enter.\nNo necesita usar el portapapeles del anfitrión.\nlabctl reset es LOCAL. labctl reset-all afecta TODA el aula: coordinar.\n' >/home/student/Desktop/LEEME-guias.txt
chown student:student /home/student/Desktop/LEEME-guias.txt
chmod +x /home/student/Desktop/*.desktop
chown student:student /home/student/Desktop/*.desktop /home/student/.vnc/xstartup
printf '\nRetail OT: labctl guides para guías locales; status e inventory para verificar.\nCopiar en Firefox y pegar en Terminal con Ctrl+Shift+V.\n' >/etc/motd
su student -c 'tigervncserver :1 -geometry 1440x900 -depth 24 -localhost yes -SecurityTypes None'
websockify --web=/usr/share/novnc 6080 localhost:5901 >/evidence/novnc.log 2>&1 &
osqueryd --logger_plugin=filesystem --config_path=/opt/retail/osquery.conf --logger_path=/evidence/osquery --database_path=/tmp/osquery.db --disable_events=true --host_identifier=hostname --logger_stderr=false >/evidence/osquery.log 2>&1 &
exec python /opt/retail/agent.py
