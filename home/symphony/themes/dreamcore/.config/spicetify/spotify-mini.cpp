// Small MPRIS controller for the official Spotify client. No account/profile access.
#include <QtWidgets>
#include <QtDBus>
#include <QtNetwork>

static const QString service = "org.mpris.MediaPlayer2.spotify";
static const QString path = "/org/mpris/MediaPlayer2";
static const QString playerInterface = "org.mpris.MediaPlayer2.Player";

class SpotifyMini final : public QWidget {
    Q_OBJECT
    QDBusInterface player{service, path, playerInterface};
    QDBusInterface properties{service, path, "org.freedesktop.DBus.Properties"};
    QNetworkAccessManager network;
    QLabel *cover = new QLabel("♪"), *title = new QLabel, *artist = new QLabel;
    QToolButton *play = new QToolButton;
    QSlider *volume = new QSlider(Qt::Horizontal);
    QString artwork;
    double currentVolume = 0;

    QIcon mediaIcon(QStyle::StandardPixmap type) {
        QPixmap image(24,24); image.fill(Qt::transparent);
        QPainter painter(&image); painter.setRenderHint(QPainter::Antialiasing);
        painter.setPen(Qt::NoPen); painter.setBrush(palette().color(QPalette::WindowText));
        if (type == QStyle::SP_MediaPause) {
            painter.drawRect(6,5,4,14); painter.drawRect(14,5,4,14);
        } else if (type == QStyle::SP_MediaPlay) {
            painter.drawPolygon(QPolygonF{QPointF(7,4),QPointF(7,20),QPointF(21,12)});
        } else {
            if (type == QStyle::SP_MediaSkipBackward) {painter.translate(24,0);painter.scale(-1,1);}
            painter.drawPolygon(QPolygonF{QPointF(3,5),QPointF(3,19),QPointF(11,12)});
            painter.drawPolygon(QPolygonF{QPointF(11,5),QPointF(11,19),QPointF(19,12)});
            painter.drawRect(20,5,3,14);
        }
        return QIcon(image);
    }

    QVariant propertyValue(const QString &name) {
        QDBusReply<QDBusVariant> reply = properties.call("Get", playerInterface, name);
        return reply.isValid() ? reply.value().variant() : QVariant();
    }
    void setVolume(double value) {
        currentVolume = qBound(0.0, value, 1.0);
        properties.asyncCall("Set", playerInterface, "Volume", QVariant::fromValue(QDBusVariant(currentVolume)));
        QSignalBlocker blocker(volume);
        volume->setValue(qRound(currentVolume * 100));
    }
    void updateArtwork(const QString &url) {
        if (artwork == url) return;
        artwork = url;
        QUrl target(url);
        if (target.scheme() != "https" || !target.host().endsWith("scdn.co")) {
            cover->setText("♪"); return;
        }
        auto *reply = network.get(QNetworkRequest(target));
        connect(reply, &QNetworkReply::finished, this, [this, reply, url] {
            if (reply->error() == QNetworkReply::NoError && artwork == url) {
                QPixmap image; image.loadFromData(reply->readAll());
                cover->setPixmap(image.scaled(112,112,Qt::KeepAspectRatio,Qt::SmoothTransformation));
            }
            reply->deleteLater();
        });
    }
public:
    SpotifyMini() {
        setWindowTitle("Spotify Mini · Dreamcore");
        resize(480,190);
        auto *layout = new QHBoxLayout(this); layout->setContentsMargins(16,16,16,16); layout->setSpacing(16);
        cover->setFixedSize(112,112); cover->setAlignment(Qt::AlignCenter); layout->addWidget(cover);
        auto *details = new QVBoxLayout; layout->addLayout(details,1);
        title->setTextFormat(Qt::PlainText); artist->setTextFormat(Qt::PlainText);
        title->setWordWrap(true); artist->setWordWrap(true);
        title->setObjectName("trackTitle"); artist->setObjectName("trackArtist");
        details->addWidget(title); details->addWidget(artist);
        auto *buttons = new QHBoxLayout; buttons->setAlignment(Qt::AlignLeft); details->addLayout(buttons);
        for (const auto &entry : {qMakePair(QString("Previous"), QStyle::SP_MediaSkipBackward),
                                 qMakePair(QString("PlayPause"), QStyle::SP_MediaPlay),
                                 qMakePair(QString("Next"), QStyle::SP_MediaSkipForward)}) {
            auto *button = entry.first == "PlayPause" ? play : new QToolButton;
            button->setIcon(mediaIcon(entry.second)); button->setIconSize(QSize(24,24));
            button->setToolTip(entry.first); buttons->addWidget(button);
            connect(button,&QToolButton::clicked,this,[this, method=entry.first]{player.asyncCall(method);});
        }
        volume->setRange(0,100); volume->setSingleStep(2); volume->installEventFilter(this);
        details->addWidget(volume);
        connect(volume,&QSlider::valueChanged,this,[this](int value){setVolume(value/100.0);});
        QFile paletteFile(QDir::homePath()+"/.config/symphony/current/palette.json");
        if (paletteFile.open(QIODevice::ReadOnly)) {
            auto colors=QJsonDocument::fromJson(paletteFile.readAll()).object();
            setStyleSheet(QString("QWidget{background:%1;color:%2;font-family:'Noto Sans';font-size:16px;}"
                "QToolButton{background:%1;color:%2;border:1px solid %5;border-radius:8px;padding:8px;}"
                "QToolButton:hover{background:%1;border-color:%2;} QLabel#trackTitle{font-weight:bold;}"
                "QSlider::groove:horizontal{height:5px;background:%1;border:1px solid %5;border-radius:2px;}"
                "QSlider::sub-page:horizontal{background:%2;}"
                "QSlider::handle:horizontal{background:%2;width:12px;margin:-4px 0;border-radius:6px;}")
                .arg(colors["background"].toString(),colors["text"].toString(),colors["panel"].toString(),
                     colors["selection"].toString(),colors["secondary_accent"].toString()));
        }
        QDBusConnection::sessionBus().connect(service,path,"org.freedesktop.DBus.Properties","PropertiesChanged",
            this,SLOT(changed(QString,QVariantMap,QStringList)));
        auto *watcher=new QDBusServiceWatcher(service,QDBusConnection::sessionBus(),QDBusServiceWatcher::WatchForOwnerChange,this);
        connect(watcher,&QDBusServiceWatcher::serviceOwnerChanged,this,[this]{refresh();});
        refresh();
    }
protected:
    bool eventFilter(QObject *object, QEvent *event) override {
        if (object == volume && event->type() == QEvent::Wheel) {
            auto *wheel=static_cast<QWheelEvent*>(event);
            const double step=wheel->modifiers().testFlag(Qt::ControlModifier)?.01:
                              wheel->modifiers().testFlag(Qt::ShiftModifier)?.05:.02;
            setVolume(currentVolume + (wheel->angleDelta().y()>0 ? step : -step));
            wheel->accept(); return true;
        }
        return QWidget::eventFilter(object,event);
    }
private slots:
    void changed(const QString &interface, const QVariantMap &, const QStringList &) {
        if (interface == playerInterface) refresh();
    }
    void refresh() {
        if (!QDBusConnection::sessionBus().interface()->isServiceRegistered(service)) {
            title->setText("Открой Spotify");artist->clear();return;
        }
        const auto metadata=qdbus_cast<QVariantMap>(propertyValue("Metadata"));
        title->setText(metadata.value("xesam:title").toString());
        artist->setText(metadata.value("xesam:artist").toStringList().join(" · "));
        play->setIcon(mediaIcon(propertyValue("PlaybackStatus").toString()=="Playing" ? QStyle::SP_MediaPause : QStyle::SP_MediaPlay));
        currentVolume=propertyValue("Volume").toDouble();
        {QSignalBlocker blocker(volume);volume->setValue(qRound(currentVolume*100));}
        updateArtwork(metadata.value("mpris:artUrl").toString());
    }
};

int main(int argc,char **argv) {
    QApplication app(argc,argv);
    app.setApplicationName("dreamcore-spotify-mini");
    app.setDesktopFileName("dreamcore-spotify-mini");
    SpotifyMini window; window.show(); return app.exec();
}
#include "spotify-mini.moc"
