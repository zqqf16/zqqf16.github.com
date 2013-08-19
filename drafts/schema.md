---
title: OpenLDAP添加Schema（Ubuntu）
date: 2013-8-19
tags: OpenLDAP
---

前言
---
工作中遇到了需要给LDAP添加自定义字段的情况，介于公司中此技艺已经失传，只能自己来了。

网络上很多流传的教程都太老了，不是很适用。Ubuntu8.10以及之后的系统倾向于用slapd-config的各种工具来配置sladp，而不是之前的直接修改文件的方法。

用sldap-config来添加Schema可以总结为以下几步：

1. 创建Schema文件
2. 将Schema转换成ldif格式文件
3. 将ldif文件内容导入

具体步骤
-------

1. 编辑Schema文件，保存为`test.schema`
		
		objectIdentifier testOID 1.1.1.1
		objectIdentifier testAttr testOID:1
		objectIdentifier testObject testOID:2
		
		attributetype ( testAttr
			NAME 'testattr'
			DESC 'Test attribute'
			EQUALITY caseIgnoreMatch
			SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 )
			
		objectclass ( testObject
			NAME 'testObject'
			DESC 'Just for test'
			AUXILIARY
			MAY	(testattr))
        
2. 创建文件`tmp.conf`,加入以下内容

		include test.schema
    
3. 创建目录`ldif_dir`

		$mkdir ldif_dir


4. 生成‘ldif’文件
	
		$slaptest -f tmp.conf -F ldif_dir

	ldif目录结构如下：
	
		.
		|-- cn=config
		|   |-- cn=schema
		|   |   `-- cn={0}test.ldif
		|   |-- cn=schema.ldif
		|   |-- olcDatabase={0}config.ldif
		|   `-- olcDatabase={-1}frontend.ldif
		`-- cn=config.ldif
		
5. 文件`cn=config/cn=schema/cn={0}test.ldif`就是生成的‘ldif’文件，编辑此文件：

	将
	
		dn: cn={0}test
		objectClass: olcSchemaConfig
		cn: {0}test
    
	修改为

		dn: cn=test,cn=schema,cn=config
    	objectClass: olcSchemaConfig
    	cn: test
    
	删除以下几行：
		
		structuralObjectClass: olcSchemaConfig
		entryUUID: 9530cb4a-9845-1032-9b5c-15d9e32663bc
		creatorsName: cn=config
		createTimestamp: 20130813092213Z
		entryCSN: 20130813092213.368308Z#000000#000#000000
		modifiersName: cn=config
		modifyTimestamp: 20130813092213Z

	最终文件变为

		dn: cn=test,cn=schema,cn=config
		objectClass: olcSchemaConfig
		cn: test
		olcObjectIdentifier: {0}testOID 1.1.1.1
		olcObjectIdentifier: {1}testAttr testOID:1
		olcObjectIdentifier: {2}testObject testOID:2
		olcAttributeTypes: {0}( testAttr NAME 'testattr' DESC 'Test attribute' E    QUALIT Y caseIgnoreMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 )
		olcObjectClasses: {0}( testObject NAME 'testObject' DESC 'Just for test'     AUXILIARY MAY testattr )

6. 将‘ldif’文件内容导入ldap数据库

		$sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f cn\=test.ldif

7. 检查导入结果

		$sudo ldapsearch -Q -LLL -Y EXTERNAL -H ldapi:/// -b cn=schema,cn=config dn
