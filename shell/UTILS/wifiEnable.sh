echo "configure wifi"
ifconfig wlp1s0 up
sleep 2
wpa_supplicant -i wlp1s0 -Dnl80211 -c /etc/wpa_supplicant.conf &
sleep 2
udhcpc -i wlp1s0
sleep 2
