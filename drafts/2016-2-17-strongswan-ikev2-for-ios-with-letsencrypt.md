---
layout: post
title: 用 Let‘s Encrypt 证书搭建 IKEv2 VPN
date: 2016-2-17
tags:
    - IKEv2
    - strongSwan
    - Let‘s Encrypt
image: 
    feature: https://z_blog.oss-cn-hangzhou.aliyuncs.com/blog/letsencrypt.png?x-oss-process=style/jpg
excerpt: >
    Let‘s Encrypt 提供的证书不仅免费而且方便，可以简化 VPN 的搭建流程
---


## 前言

之前写过一遍博客，[用 strongSwan 搭建免证书的 IKEv2 VPN](/strongswan-ikev2-for-ios-without-certificate/)，之所以不想用证书，主要是因为买证书需要钱，而生成证书的手续又过于繁琐。需要创建个 CA，然后签发证书，客户端还得手动信任 CA，中间过程很容易出错。

现在有了 [Let‘s Encrypt](https://letsencrypt.org)，问题简单多了。它不仅可以提供免费的受信证书，而且用起来很简单。另外，用了证书认证之后，在 iOS 上就免除了安装配置文件的步骤。

简直 “**完美**”👈👩👉

## 服务器端配置

#### 1. 安装 strongSwan

请参考: [用 strongSwan 搭建免证书的 IKEv2 VPN](/strongswan-ikev2-for-ios-without-certificate/)。

#### 2. 申请 Let's Encrypt 证书

这步超级简单：

``` shell
user@webserver:~$ git clone https://github.com/letsencrypt/letsencrypt
user@webserver:~$ cd letsencrypt
user@webserver:~/letsencrypt$ ./letsencrypt-auto certonly --standalone
```

注意：填写的域名必须跟 VPN 服务器地址一致。

生成的证书位于 /etc/letsencrypt/archive/your.domain/ 目录下，需要拷贝到 strongSwan 目录：

``` shell
cp /etc/letsencrypt/live/your.domain/fullchain.pem /etc/ipsec.d/certs
cp /etc/letsencrypt/live/your.domain/privkey.pem /etc/ipsec.d/private
```

#### 3. 修改 /etc/ipsec.conf 配置

如下：

``` 
# ipsec.conf - strongSwan IPsec configuration file
# basic configuration
config setup
    strictcrlpolicy=no
    uniqueids = no

# Default
conn %default
    keyexchange=ikev2
    auto=add
    dpdaction=clear
    leftsubnet=0.0.0.0/0
    right=%any
    rightsourceip=10.99.1.0/24

# With certificate
conn iOS-IKEv2-cert
    leftid=your.domain
    leftcert=fullchain.pem
    leftsendcert=always
    rightauth=eap-mschapv2
    eap_identity=%identity
```

注意：leftid 需要跟你的域名一致。

#### 4. 修改 /etc/ipsec.secret 文件

``` 
: RSA privkey.pem
u1 : EAP "password"
u2 : EAP "password"
```

#### 5. 配置 IP Table

``` bash
#!/bin/bash

# Add ip tables

iptables -A INPUT -p udp --dport 500 -j ACCEPT
iptables -A INPUT -p udp --dport 4500 -j ACCEPT
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A POSTROUTING -s 10.99.1.0/24 -o eth0 -j MASQUERADE
iptables -A FORWARD -s 10.99.1.0/24 -j ACCEPT
```

#### 6. 启动 ipsec

``` bash
ipsec start
```

## 客户端配置

#### 1. 添加 VPN 配置

进入“设置” -> “VPN” -> “添加 VPN 配置”，选择 “IKEv2” 类型，填好参数保存。

#### 2. 安装 Let‘s Encrypt 中间证书

用 Safari 访问 [https://letsencrypt.org](https://letsencrypt.org/certificates/)，点击 **PEM** 格式的 **Let’s Encrypt Authority X1** 证书并安装。

至此，就可以连接 VPN 了。

## 参考链接

[Strongswan on Ubuntu 16.04 for iOS 9 Client](http://dcamero.azurewebsites.net/strongswan-ubuntu-1604-ios-9.html)