title: 初识 iBeacon
date: 2014-9-1
tag: iOS
tag: iBeacon

以前玩 Arduino 的时候就了解过蓝牙4.0，当时颇让我震惊的是它仅用一颗纽扣电池就可以工作一年！这天生就就是为物联网以及可穿戴设备准备的。可惜当时各厂商对它的支持不是很广泛，只有 iPhone 以及少数 Android 手机支持，一个小小的开发模块也得一两百大洋。

后来看 WWDC 2014的视频（2013年没注意...），了解到了 iBeacon，一个苹果基于蓝牙4.0开发的定位技术。

大致原理如下：

iBeacon 基站每隔一段时间就向周围广播，信息里面带有自己的 UUID 以及 Major 和 Minor。当一个 iOS 设备进入此基站的覆盖范围，通过这三个维度就可验证一个基站的身份。然后通过应用程序来进行下一步的行动。

比如，商场在每一个店铺里都部署了 iBeacon 基站。消费者装上商场的应用之后，每当走近一个店铺，应用都会被唤醒，给用户发送通知，告诉用户此店铺的打折促销活动等等。

在此过程中，基站不做任何工作，一切行为都是由 APP 控制的。APP 告诉 iOS 监听那些 UUID，当 iOS 收到消息后，会通知 APP 来处理。在 iOS 中，即使 APP 并不在运行，系统收到消息后也会调用 APP 来处理。

并且，所有的 iBeacon 探测功能都是由系统完成的，避免了 APP 过多的消耗电能。这也是很多 Android 上的实现方案所不具备的。

了解了这些知识之后，兴趣来了，于是就上淘宝买了个四月兄弟开发的 iBeacon。

![](http://zorro-blog.qiniudn.com/IMG_0791.JPG)
体积超小，可以轻松地用双面胶黏在墙上

再看看内部结构
![](http://zorro-blog.qiniudn.com/IMG_0793.JPG)

比一颗2450纽扣电池大不了多少~

接下来就是尝试应用开发了。

首先，创建一个应用，需要依赖`CoreLocation.framework`。并且在 View Controller 的实现文件里加上：

```objective-c
#import <CoreLocation/CoreLocation.h>
```

然后加上两个 Property：

```objective-c
@property (nonatomic, strong) CLBeaconRegion *beaconRegion;
@property (nonatomic, strong) CLLocationManager *locationManager;
```

`beaconRegion` 用来定义一个 Beacon，iOS 的 iBeacon API 中，应用只能探测已知 UUID 的 iBeacon 基站。要想探测周围所有基站，就得用底层的 Bluetooth 库或者 iBeacon 基站厂商提供的 SDK。
`localtionManager` 用来进行实际的探测工作。

接下来定义 Beacon 初始化方法：

```objective-c
- (void)initBeacon {
    NSUUID *uuid = [[NSUUID alloc] initWithUUIDString:@"E2C56DB5-DFFB-48D2-B060-D0F5A71096E0"];
    self.beaconRegion = [[CLBeaconRegion alloc] initWithProximityUUID:uuid identifier:@"E2C56DB5-DFFB-48D2-B060-D0F5A71096E0"];
    
    self.beaconRegion = [[CLBeaconRegion alloc] initWithProximityUUID:uuid major:0 minor:0 identifier:@"im.zorro.ibeacon"];
    
    self.locationManager = [[CLLocationManager alloc] init];
    _locationManager.delegate = self;
    [_locationManager startMonitoringForRegion:_beaconRegion];
    [_locationManager startRangingBeaconsInRegion:_beaconRegion];
    
    if([[[UIDevice currentDevice] systemVersion] floatValue] >= 8.0) {
        [self.locationManager requestAlwaysAuthorization];
    }
}

```

这段代码首先初始化了一个 Beacon Region，UUID、Major 以及 Minor 是我通过四月兄弟提供的 APP 获取的， 这里因厂商而异。

接着初始化了 Location Manager，把 Delegate 设置成当前 View Controller。（需要实现`CLLocationManagerDelegate`协议）

这里有一点需要说明，在 iOS 8中，使用 Location Manager 需要申请授权，也就是调用`- (void)requestAlwaysAuthorization`这个方法，这是 iOS 8 新加的。
同时，需要在 Info.plist 里加上两个 Key：

```
NSLocationWhenInUseUsageDescription
NSLocationAlwaysUsageDescription
```

这样，在程序第一次运行的时候，会有这样的提示：

![](http://zorro-blog.qiniudn.com/IMG_0795.PNG)

我之前没有注意到这一点，导致死活探测不到基站...

初始化完成之后，我们需要处理事件，也就是实现`CLLocationManagerDelegate`协议。主要代码如下：

```objective-c
- (void)locationManager:(CLLocationManager *)manager didEnterRegion:(CLRegion *)region {
    [self.locationManager startRangingBeaconsInRegion:self.beaconRegion];
}

-(void)locationManager:(CLLocationManager *)manager didExitRegion:(CLRegion *)region {
    [self.locationManager stopRangingBeaconsInRegion:self.beaconRegion];
}

- (void)locationManager:(CLLocationManager *)manager monitoringDidFailForRegion:(CLRegion *)region withError:(NSError *)error {
    NSLog(@"Failed monitoring region: %@", error);
}

- (void)locationManager:(CLLocationManager *)manager didFailWithError:(NSError *)error {
    NSLog(@"Location manager failed: %@", error);
}

-(void)locationManager:(CLLocationManager *)manager didRangeBeacons:(NSArray *)beacons inRegion:(CLBeaconRegion *)region {
    CLBeacon *beacon = [[CLBeacon alloc] init];
    beacon = [beacons lastObject];
    
    NSLog(@"##Beacon is %@", beacon);
    
    _uuid.text = beacon.proximityUUID.UUIDString;
    _major.text = [beacon.major stringValue];
    _minor.text = [beacon.minor stringValue];

    _proximity.text = @[@"Unknow", @"Immediate", @"Near", @"Far"][beacon.proximity];
}

```

其中`locationManager: didRangeBeacons: inRegion:` 方法在每次 iOS 探测之后都会被调用，频率大约是每秒一次。此方法会得到探测到的基站信息，里面包括了 UUID、Major、Minor、以及 Proximity 和 rssi 等。

Proximity 代表了与基站的距离，由于2.4G 信号也不怎么靠谱，容易受干扰，所以测出来的距离不是那么准确。Apple 用了四个值代表距离，分别是 Immediate、Near、Far、Unknow，距离依次递减。根据我的测试，在1m 以内基本上就是 Immediate，1米到3米就是 Near。

Log 打印如下:
```##Beacon is CLBeacon (uuid:<__NSConcreteUUID 0x15595ac0> E2C56DB5-DFFB-48D2-B060-D0F5A71096E0, major:0, minor:0, proximity:1 +/- 0.26m, rssi:-47)
```

上一张截图：
![](http://zorro-blog.qiniudn.com/IMG_0794.PNG)

<s>最后，发现了一个好玩的东西。在OS X 10.10发布的时候，Apple 着重介绍了与 iOS 8 联动功能。比如，拿着 iPhone 走近正在浏览网页的 Mac，iPhone 的锁屏界面左下角就会出现 Safari 图标，划开之后就能打开该网页。 

就在刚才我玩 iBeacon 的时候，似乎发现了一个秘密——这功能是通过 iBeacon 实现的！

看这张截图：
![](http://zorro-blog.qiniudn.com/IMG_0796.PNG)

左下角出现了我的测试应用的图标！而且划开之后就是我的测试应用~

这也就解释了为啥拿着手机进星巴克，左下角会有星巴克应用的图标，因为他们部署了 iBeacon~</s>

好吧，火星了，昨晚兴致勃勃地以为发现了事实的真相，结果一搜，连百度都能搜的出来…

哈哈
