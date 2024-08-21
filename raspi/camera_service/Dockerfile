# Example Dockerfile using motion
FROM ccrisan/motioneye:master-armhf

COPY start_camera.sh /start_camera.sh
COPY motion.conf /etc/motion/motion.conf

CMD ["sh", "/start_camera.sh"]
