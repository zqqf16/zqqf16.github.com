---
layout: post
title: 用 strongSwan 搭建免证书的 IKEv2 VPN
date: 2015-10-14
tags:
    - IKEv2
    - strongSwan
image:
    feature: https://z_blog.oss-cn-hangzhou.aliyuncs.com/blog/Strongswan.png?x-oss-process=style/jpg
excerpt: >
    目前能搜到的 strongSwan IKEv2 配置基本上都是基于证书的，不知道别人怎么样，反正我觉得证书方式挺繁琐的，虽然跟证书打了三年多的交道。
    如果只是在 iOS 或者 OS X 上用 IKEv2，用 PSK（预共享密钥）的方式就简单很多。
---

## 前言

目前能搜到的 strongSwan IKEv2 配置基本上都是基于证书的，不知道别人怎么样，反正我觉得证书方式挺繁琐的，虽然跟证书打了三年多的交道。

如果只是在 iOS 或者 OS X 上用 IKEv2，用 PSK（预共享密钥）的方式就简单很多。

*本文仅限于科学研究使用，请勿用于其他目的。所有配置文件可以在 [Gist](https://gist.github.com/zqqf16/b207a17637de103e05c6) 上获取。*

## 服务端配置

### 1. 安装 strongSwan

我是在 Ubuntu 下安装的，如果图省事，可以直接 `apt-get install strongSwan` 搞定，源里的版本已经是 5.x 了，不算太旧。

如果想安装最新的，可以自行下载编译。

``` bash
# Download strongSwan
wget https://download.strongswan.org/strongswan-5.3.3.tar.gz

# Extract and uncompress
tar -vzxf strongswan-5.3.3.tar.gz
cd strongswan-5.3.3

# Configure
./configure --prefix=/usr --sysconfdir=/etc  --enable-openssl --enable-nat-transport --disable-mysql --disable-ldap  --disable-static --enable-shared --enable-md4 --enable-eap-mschapv2 --enable-eap-aka --enable-eap-aka-3gpp2  --enable-eap-gtc --enable-eap-identity --enable-eap-md5 --enable-eap-peap --enable-eap-radius --enable-eap-sim --enable-eap-sim-file --enable-eap-simaka-pseudonym --enable-eap-simaka-reauth --enable-eap-simaka-sql --enable-eap-tls --enable-eap-tnc --enable-eap-ttls

# If configure error: "GNU Multiprecision Library GMP not found"
# apt-get install libgmp3-dev

# Make & install
make && make install
```

### 2. strongSwan 配置

编辑 /etc/ipsec.conf

``` config
# ipsec.conf - strongSwan IPsec configuration file
# basic configuration
config setup
    strictcrlpolicy=no
    uniqueids = no

# IKEv2 for iOS
conn iOS-IKEV2
    auto=add
    dpdaction=clear
    keyexchange=ikev2
    #left
    left=%any
    leftsubnet=0.0.0.0/0
    leftauth=psk
    leftid=im.zorro.ipsec.server
    #right
    right=%any
    rightsourceip=10.99.1.0/24
    rightauth=eap-mschapv2
    rightid=im.zorro.ipsec.client
```

需要注意的点是 `leftauth=psk` 与 `rightauth=eap-mschapv2`，分别对应着 iOS／OS X 中的“设备鉴定”与“EAP 鉴定”。

“rightauth” 的方法有很多，比如 “eap-md5” 这样的，iOS 不一定能支持，有时间的可以多尝试几个～

*PS：个人觉得 Apple 的命名方式比 strongSwan 的 left 和 right 容易理解多了。*

至于 `rightsourceip`，根据使用者的网络情况，别跟客户端子网冲突了就行，比如 `172.16.x.x`、`10.x.x.x`、`192.168.x.x`。

`leftid` 与 `rightid` 分别对应着**远程标识符**（RemoteIdentifier）和**局部标识符**（LocalIdentifier），随便选个顺眼的即可。

### 3. PSK 与用户名密码

编辑 /etc/ipsec.secrets

``` config
: PSK yourpresharedkey
u1 : EAP "password"
u2 : EAP "password"
```

`: PSK yourpresharedkey` 这行要填预共享密钥，下面的 u1、u2 是添加的两个用户。

### 4. 配置 IP Table

执行以下代码：

``` bash
#!/bin/bash

# Add ip tables

iptables -A INPUT -p udp --dport 500 -j ACCEPT
iptables -A INPUT -p udp --dport 4500 -j ACCEPT
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A POSTROUTING -s 10.99.1.0/24 -o eth0 -j MASQUERADE
iptables -A FORWARD -s 10.99.1.0/24 -j ACCEPT
```

注意：**网段要跟 ipsec.conf 里配置的一致**。

### 5. 配置 DNS

编辑 /etc/strongswan.conf

``` config
charon {
        load_modular = yes
        dns1 = 8.8.8.8
        dns2 = 8.8.4.4
        plugins {
                include strongswan.d/charon/*.conf
        }
}

include strongswan.d/*.conf
```

### 6. 启动 strongSwan

启动：`ipsec start`

重新加载配置文件：`ipsec reload`

重新加载用户名密码文件：`ipsec rereadsecrets`

## 客户端配置

虽然从 iOS 9 开始，系统设置中可以手动添加 IKEv2 配置了，但是没法输入 PSK，也不知道 Apple 咋想的。

最靠谱的方式还是用配置文件方式，推荐用 Apple Configurator。

其中：

* **设备鉴定**选择**共享密钥**
* 勾上**启用 EAP**
* **EAP 鉴定**选择**用户名/密码**

*<s>PS：我用 Apple Configurator 2，可能是 Beta 的缘故，编辑的时候总是提示有错误，却死活找不着错误的地方……</s>已更新*

如果没有 Apple Configurator，可以手工编辑下面的文件：

``` plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>PayloadContent</key>
	<array>
		<dict>
			<key>IKEv2</key>
			<dict>
				<key>AuthName</key>
				<string>{username}</string>
				<key>AuthPassword</key>
				<string>{password}</string>
				<key>AuthenticationMethod</key>
				<string>SharedSecret</string>
				<key>ChildSecurityAssociationParameters</key>
				<dict>
					<key>DiffieHellmanGroup</key>
					<integer>2</integer>
					<key>EncryptionAlgorithm</key>
					<string>3DES</string>
					<key>IntegrityAlgorithm</key>
					<string>SHA1-96</string>
					<key>LifeTimeInMinutes</key>
					<integer>1440</integer>
				</dict>
				<key>DeadPeerDetectionRate</key>
				<string>Medium</string>
				<key>DisableMOBIKE</key>
				<integer>0</integer>
				<key>DisableRedirect</key>
				<integer>0</integer>
				<key>EnableCertificateRevocationCheck</key>
				<integer>0</integer>
				<key>EnablePFS</key>
				<integer>0</integer>
				<key>ExtendedAuthEnabled</key>
				<true/>
				<key>IKESecurityAssociationParameters</key>
				<dict>
					<key>DiffieHellmanGroup</key>
					<integer>2</integer>
					<key>EncryptionAlgorithm</key>
					<string>3DES</string>
					<key>IntegrityAlgorithm</key>
					<string>SHA1-96</string>
					<key>LifeTimeInMinutes</key>
					<integer>1440</integer>
				</dict>
				<key>LocalIdentifier</key>
				<string>{rightid}</string>
				<key>RemoteAddress</key>
				<string>{your_server_address}</string>
				<key>RemoteIdentifier</key>
				<string>{leftid}</string>
				<key>SharedSecret</key>
				<string>{your_psk}</string>
				<key>UseConfigurationAttributeInternalIPSubnet</key>
				<integer>0</integer>
			</dict>
			<key>IPv4</key>
			<dict>
				<key>OverridePrimary</key>
				<integer>1</integer>
			</dict>
			<key>PayloadDescription</key>
			<string>Configures VPN settings</string>
			<key>PayloadDisplayName</key>
			<string>VPN</string>
			<key>PayloadIdentifier</key>
			<string>com.apple.vpn.managed.FBFBDEF8-5B16-4863-91C1-7E2A68F848A3</string>
			<key>PayloadType</key>
			<string>com.apple.vpn.managed</string>
			<key>PayloadUUID</key>
			<string>425A1628-E99B-4547-966E-5B967CF1F5EA</string>
			<key>PayloadVersion</key>
			<real>1</real>
			<key>Proxies</key>
			<dict>
				<key>HTTPEnable</key>
				<integer>0</integer>
				<key>HTTPSEnable</key>
				<integer>0</integer>
			</dict>
			<key>UserDefinedName</key>
			<string>JP</string>
			<key>VPNType</key>
			<string>IKEv2</string>
			<key>VendorConfig</key>
			<dict/>
		</dict>
	</array>
	<key>PayloadDisplayName</key>
	<string>IKEv2</string>
	<key>PayloadIdentifier</key>
	<string>C7918ABA-8DE8-40ED-A3AE-994CD40ACE22</string>
	<key>PayloadRemovalDisallowed</key>
	<false/>
	<key>PayloadType</key>
	<string>Configuration</string>
	<key>PayloadUUID</key>
	<string>9697F3C2-FF20-4981-A0C4-AA36BA78EEEA</string>
	<key>PayloadVersion</key>
	<integer>1</integer>
</dict>
</plist>
```

保存成 .mobileconfig 格式，发到手机里安装就可以了。

## 参考链接

* [linux上用strongswan搭建ikev2协议vpn](https://gist.github.com/losisli/11081793)
* [strongSwan configuration](https://wiki.strongswan.org/projects/strongswan/wiki/ConnSection)