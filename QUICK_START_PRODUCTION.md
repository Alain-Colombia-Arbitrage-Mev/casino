# 🚀 Quick Start - AI Casino en Producción

## ⚡ Guía Rápida de 15 Minutos

### 1. Preparar Servidor (5 minutos)

```bash
# Conectar a tu VPS
ssh root@tu-servidor.com

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configurar firewall
ufw allow ssh && ufw allow 80 && ufw allow 443 && ufw --force enable
```

### 2. Desplegar Aplicación (5 minutos)

```bash
# Clonar proyecto
git clone tu-repositorio /opt/aicasino
cd /opt/aicasino

# Configurar variables
cp .env.production.example .env.production
nano .env.production
# Editar: DOMAIN, REDIS_PASSWORD, SSL_EMAIL

# Hacer scripts ejecutables
chmod +x scripts/*.sh

# Deploy automático
./scripts/deploy.sh
```

### 3. Configurar SSL (5 minutos)

```bash
# Instalar Certbot
snap install --classic certbot

# Obtener certificado SSL
certbot certonly --standalone -d tu-dominio.com -d www.tu-dominio.com

# Copiar certificados
mkdir -p /opt/aicasino/ssl
cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem /opt/aicasino/ssl/
cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem /opt/aicasino/ssl/

# Reiniciar Nginx
docker-compose -f docker-compose.production.yml restart nginx
```

---

## 🎯 Verificación Rápida

### Comprobar Servicios
```bash
cd /opt/aicasino
docker-compose -f docker-compose.production.yml ps
```

### URLs de Verificación
- **Frontend**: https://tu-dominio.com
- **Backend API**: https://tu-dominio.com/api/health
- **ML API**: https://tu-dominio.com/ml-api/health

### Comandos Útiles
```bash
# Ver logs en tiempo real
docker-compose -f docker-compose.production.yml logs -f

# Reiniciar todo el sistema
docker-compose -f docker-compose.production.yml restart

# Monitoreo del sistema
./scripts/monitor.sh

# Backup manual
./scripts/backup.sh
```

---

## 🔧 Configuración Automática

### Cron Jobs (Automatización)
```bash
# Editar crontab
crontab -e

# Agregar líneas:
*/5 * * * * /opt/aicasino/scripts/monitor.sh
0 2 * * * /opt/aicasino/scripts/backup.sh
0 0 * * 0 /opt/aicasino/scripts/deploy.sh
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📋 Checklist Post-Deployment

- [ ] ✅ Todos los contenedores corriendo
- [ ] ✅ SSL funcionando (candado verde)
- [ ] ✅ API endpoints respondiendo
- [ ] ✅ Redis con datos
- [ ] ✅ Scraper detectando números
- [ ] ✅ Frontend cargando correctamente
- [ ] ✅ Logs sin errores críticos
- [ ] ✅ Backup automático configurado
- [ ] ✅ Monitoreo activo

---

## 🆘 Solución de Problemas

### Servicio no inicia
```bash
docker-compose -f docker-compose.production.yml logs [servicio]
```

### SSL no funciona
```bash
certbot certificates
nginx -t
```

### Sin datos en Redis
```bash
docker exec aicasino-redis redis-cli keys "*"
```

### Performance lenta
```bash
htop
docker stats
```

---

## 🌐 Proveedores Recomendados

### Económicos ($20-40/mes)
- **Hetzner Cloud**: CPX21 (2 vCPU, 4GB RAM)
- **Vultr**: Regular Performance (2 vCPU, 4GB RAM)
- **Linode**: Shared CPU (2 vCPU, 4GB RAM)

### Premium ($40-80/mes)
- **DigitalOcean**: Droplet (4 vCPU, 8GB RAM)
- **AWS**: t3.medium (2 vCPU, 4GB RAM)
- **Google Cloud**: e2-standard-2 (2 vCPU, 8GB RAM)

---

## 📞 Soporte

- **Logs**: `/opt/aicasino/logs/`
- **Configuración**: `docker-compose.production.yml`
- **Monitoreo**: `./scripts/monitor.sh --report`

¡Tu AI Casino está listo en 15 minutos! 🎰✨