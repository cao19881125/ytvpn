## 部署准备(server & client)

### clone代码

```
git clone https://github.com/cao19881125/ytvpn.git
```

### build镜像

```
cd ytvpn
docker build -t cao19881125/ytvpn:latest docker/
```

### 创建配置文件

```
mkdir /etc/ytvpn
cp etc/* /etc/ytvpn/
```

## server部署
### 开启转发
#### 关闭selinux

```
sed -i 's/SELINUX.*=.*enforcing/SELINUX=disabled/g' /etc/selinux/config
reboot
```

#### 开启转发

```
# vim /etc/sysctl.conf
net.ipv4.ip_forward = 1

sysctl -p
```

#### 配置snat

```
iptables -A POSTROUTING -t nat -o eth0 -j MASQUERADE
```



### 修改配置文件

```
# vim /etc/ytvpn/server.cfg
[DEFAULT]
LISTEN_PORT:9999
LOG_LEVEL=DEBUG
BANDWIDTH=100
CLIENT_TO_CLIENT=False
SERVERIP=10.5.0.1
DHCP_POOL=10.5.0.10-20

user_file=/etc/ytvpn/user_file
```
需要注意的参数如下(可以用默认值)：
- LISTEN_PORT:服务端监听的端口
- SERVERIP:启动后服务端使用的IP
- DHCP_POOL:分配给客户端的IP



```
# vim /etc/ytvpn/user_file
[USER]
test=123456
```
- 配置用户名密码


### 启动

```
docker run -t -d --name "ytvpn-server" --network host -v /etc/ytvpn/:/etc/ytvpn/ -v /var/log/ytvpn/:/var/log/ytvpn/ --restart always --privileged cao19881125/ytvpn:latest ytvpn --run_type server --config-file /etc/ytvpn/server.cfg
```

## client部署

### 修改配置文件

```
# vim /etc/ytvpn/client.cfg
[DEFAULT]
SERVER_IP=192.168.184.139
SERVER_PORT=9999
LOG_LEVEL=DEBUG

USER_NAME=test
PASSWORD=123456
```
- SERVER_IP:服务端的IP
- SERVER_PORT:服务端监听的端口
- USER_NAME:用户名
- PASSWORD:密码

### 运行

```
docker run -t -d --name "ytvpn-client" --network host -v /etc/ytvpn/:/etc/ytvpn/ -v /var/log/ytvpn/:/var/log/ytvpn/ --restart always --privileged cao19881125/ytvpn:latest ytvpn --run_type client --config-file /etc/ytvpn/client.cfg
```

