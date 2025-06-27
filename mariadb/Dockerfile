FROM mariadb:11.1.3
RUN apt-get update
RUN apt-get install -y cron
COPY ./backup.sh /
RUN chmod +x /backup.sh
RUN echo '0 0 * * * /backup.sh' | crontab -