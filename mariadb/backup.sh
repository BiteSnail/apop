#!/bin/bash
# Backup storage directory
backupfolder=/backups #update this to your home folder
logfile=./db_backup.log #update this to your home folder
# MySQL user
user=root
# MySQL password
password=password #update this to the backup password you created
# Number of days to store the backup
keep_day=15
backupdirectory=$backupfolder/all-database-$(date +%Y-%m-%d_%H-%M-%S)
zipfile=$backupfolder/all-database-$(date +%Y-%m-%d_%H-%M-%S).zip
echo Starting Backup [$(date +%Y-%m-%d_%H-%M-%S)] >> $logfile

# Create backup folder if it doesn't exist
if [ ! -d "$backupfolder" ]; then
  mkdir -p "$backupfolder"
  echo "Backup folder created at $backupfolder" >> $logfile
fi

# Create a backup
mariadb-backup --backup --user=$user --password=$password --target-dir=$backupdirectory
if [ $? == 0 ]; then
  echo 'dump created' >> $logfile
else
  echo [error] mariadb return non-zero code $? >> $logfile
  exit
fi

# Compress backup
zip -r $zipfile $backupdirectory
if [ $? == 0 ]; then
  echo 'The backup was successfully compressed' >> $logfile
else
  echo '[error] Error compressing backup' >> $logfile
  exit
fi

rm -r $backupdirectory
echo $zipfile >> $logfile
echo Backup complete [$(date +%Y-%m-%d_%H-%M-%S)] >> $logfile
# Delete old backups
find $backupfolder -mtime +$keep_day -delete