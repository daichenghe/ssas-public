# SSAS - Simple Smart Automotive Software
# Copyright (C) 2021 Parai Wang <parai@foxmail.com>

import os
from .helper import *

__all__ = ['Gen_SomeIp']


def Gen_DemoRxTp(C, name):
    C.write('Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (
        name))
    C.write('  Std_ReturnType ret = E_OK;\n')
    C.write(
        '  if ((NULL != msg) && ((msg->offset + msg->length)) < sizeof(%sTpRxBuf)) {\n' % (name))
    C.write(
        '    memcpy(&%sTpRxBuf[msg->offset], msg->data, msg->length);\n' % (name))
    C.write('    if (FALSE == msg->moreSegmentsFlag) {\n')
    C.write('      msg->data = %sTpRxBuf;\n' % (name))
    C.write('    }\n')
    C.write('  } else {\n')
    C.write('    ret = E_NOT_OK;\n')
    C.write('  }\n')
    C.write('  return ret;\n')
    C.write('}\n\n')


def Gen_DemoTxTp(C, name):
    C.write('Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (
        name))
    C.write('  Std_ReturnType ret = E_OK;\n')
    C.write(
        '  if ((NULL != msg) && ((msg->offset + msg->length) < sizeof(%sTpTxBuf))) {\n' % (name))
    C.write(
        '    memcpy(msg->data, &%sTpTxBuf[msg->offset], msg->length);\n' % (name))
    C.write('  } else {\n')
    C.write('    ret = E_NOT_OK;\n')
    C.write('  }\n')
    C.write('  return ret;\n')
    C.write('}\n\n')


def Gen_MethodRxTxTp(C, service, method):
    Gen_DemoRxTp(C, '%s_%s' % (service['name'], method['name']))
    Gen_DemoTxTp(C, '%s_%s' % (service['name'], method['name']))


def Gen_ServerServiceExCpp(service, dir):
    C = open('%s/SS_Ex%s.cpp' % (dir, service['name']), 'w')
    GenHeader(C)
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('#include "usomeip/usomeip.hpp"\n')
    C.write('#include "usomeip/server.hpp"\n')
    C.write('extern "C" {\n')
    C.write('#include "SS_%s.h"\n' % (service['name']))
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('#include "Sd_Cfg.h"\n')
    C.write('}\n')
    C.write('#include "plugin.h"\n')
    C.write('#include "Std_Timer.h"\n')
    C.write('using namespace as;\n')
    C.write('using namespace as::usomeip;\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write('class SS_%s;\n' % (service['name']))
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    C.write('static std::shared_ptr<SS_%s> SS_Instance = nullptr;\n' %
            (service['name']))
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.write('class SS_%s: public server::Server {\n' % (service['name']))
    C.write('public:\n')
    C.write('  SS_%s() {\n' % (service['name']))
    C.write('  }\n')
    C.write('  ~SS_%s() {\n' % (service['name']))
    C.write('  }\n')

    C.write('  void start() {\n')
    C.write('    identity(SOMEIP_SSID_%s);\n' % (service['name'].upper()))
    C.write('    offer(SD_SERVER_SERVICE_HANDLE_ID_%s);\n' % (service['name'].upper()))
    C.write('    m_BufferPool.create("SS_%s", 5, 1024 * 1024);\n' %
            (service['name']))
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('    listen(SOMEIP_RX_METHOD_%s, &m_BufferPool);\n' %
                (bName.upper()))
    for event_group in service['event-groups']:
        bName = '%s_%s' % (service['name'], event_group['name'])
        C.write('    provide(SD_EVENT_HANDLER_%s);\n' % (bName.upper()))
    C.write('    Std_TimerStart(&m_Timer);\n')
    C.write('  }\n\n')

    C.write('  void stop() {\n')
    C.write('    Std_TimerStop(&m_Timer);\n')
    C.write('  }\n\n')

    C.write('  void onRequest(std::shared_ptr<Message> msg) {\n')
    C.write('    usLOG(INFO, "%s: on request: %%s\\n", msg->str().c_str());\n' %
            (service['name']))
    C.write('    msg->reply(E_OK, msg->payload);\n')
    C.write('  }\n\n')

    C.write('  void onFireForgot(std::shared_ptr<Message> msg) {\n')
    C.write('    usLOG(INFO, "%s: on fire forgot: %%s\\n", msg->str().c_str());\n' %
            (service['name']))
    C.write('  }\n\n')

    C.write('  void onError(std::shared_ptr<Message> msg) {\n')
    C.write('  }\n\n')

    C.write('  void onSubscribe(uint16_t eventGroupId, bool isSubscribe) {\n')
    C.write('    usLOG(INFO, "%s: event group %%d %%s\\n", eventGroupId, isSubscribe ? "subscribed" : "unsubscribed");\n' % (
        service['name']))
    C.write('  }\n\n')

    C.write('  void run() {\n')
    C.write('    if (Std_GetTimerElapsedTime(&m_Timer) >= 1000000) {\n')
    C.write('      Std_TimerStart(&m_Timer);\n')
    for event_group in service['event-groups']:
        for event in event_group['events']:
            beName = '%s_%s_%s' % (
                service['name'], event_group['name'], event['name'])
            C.write('      uint32_t requestId =\n')
            C.write(
                '        ((uint32_t)SOMEIP_TX_EVT_%s << 16) + (++m_SessionId);\n' % (beName.upper()))
            C.write('      auto buffer = m_BufferPool.get();\n')
            C.write('      if (nullptr != buffer) {\n')
            C.write('        buffer->size = 8000;\n')
            C.write('        uint8_t *data = (uint8_t *)buffer->data;\n')
            C.write('        for (size_t i = 0; i < buffer->size; i++) {\n')
            C.write('          data[i] = m_SessionId + i;\n')
            C.write('        }\n')
            C.write('        notify(requestId, buffer);\n')
            C.write('      }\n')
            break
    C.write('    }\n')
    C.write('  }\n\n')

    C.write('private:\n')
    C.write('  Std_TimerType m_Timer;\n')
    C.write('  BufferPool m_BufferPool;\n')
    C.write('  uint16_t m_SessionId = 0;\n')
    C.write('};\n\n')

    C.write('void SS_Ex%s_init(void) {\n' % (service['name']))
    C.write('  SS_Instance = std::make_shared<SS_%s>();\n' % (service['name']))
    C.write('  SS_Instance->start();\n')
    C.write('}\n\n')

    C.write('void SS_Ex%s_main(void) {\n' % (service['name']))
    C.write('  SS_Instance->run();\n')
    C.write('}\n\n')

    C.write('void SS_Ex%s_deinit(void) {\n' % (service['name']))
    C.write('  SS_Instance->stop();\n')
    C.write('}\n\n')
    C.write('REGISTER_PLUGIN(SS_Ex%s);\n' % (service['name']))
    C.close()


def Gen_ServerService(service, dir):
    H = open('%s/SS_%s.h' % (dir, service['name']), 'w')
    GenHeader(H)
    H.write('#ifndef _SS_%s_H\n' % (service['name'].upper()))
    H.write('#define _SS_%s_H\n' % (service['name'].upper()))
    H.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    H.write('#include "SomeIp.h"\n')
    H.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    H.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    H.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    H.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    H.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    H.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    H.write('void SomeIp_%s_OnConnect(uint16_t conId, boolean isConnected);\n' %
            (service['name']))
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        H.write('Std_ReturnType SomeIp_%s_OnRequest(uint32_t requestId, SomeIp_MessageType* req, SomeIp_MessageType* res);\n' %
                (bName))
        H.write('Std_ReturnType SomeIp_%s_OnFireForgot(uint32_t requestId, SomeIp_MessageType* res);\n' %
                (bName))
        H.write('Std_ReturnType SomeIp_%s_OnAsyncRequest(uint32_t requestId, SomeIp_MessageType* res);\n' %
                (bName))
        if method.get('tp', False):
            H.write('Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg);\n' %
                    (bName))
            H.write('Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg);\n' %
                    (bName))
    for egroup in service['event-groups']:
        bName = '%s_%s' % (service['name'], egroup['name'])
        H.write('void SomeIp_%s_OnSubscribe(boolean isSubscribe, TcpIp_SockAddrType* RemoteAddr);\n' % (
            bName))
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            if event.get('tp', False):
                H.write('Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg);\n' %
                        (beName))
    H.write('#endif /* _SS_%s_H */\n' % (service['name'].upper()))
    H.close()
    C = open('%s/SS_%s.c' % (dir, service['name']), 'w')
    GenHeader(C)
    C.write('/* TODO: This is default demo code */\n')
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('#include "SS_%s.h"\n' % (service['name']))
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('#include "Std_Debug.h"\n')
    C.write('#include <string.h>\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write('#define AS_LOG_%s 1\n' % (service['name'].upper()))
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        if method.get('tp', False):
            C.write('static uint8_t %sTpRxBuf[%d];\n' % (
                bName, method.get('tpRxSize', 1*1024*1024)))
            C.write('static uint8_t %sTpTxBuf[%d];\n' % (
                bName, method.get('tpTxSize', 1*1024*1024)))
    for egroup in service['event-groups']:
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            if event.get('tp', False):
                C.write('static uint8_t %sTpTxBuf[%d];\n' % (
                    beName, event.get('tpTxSize', 1*1024*1024)))
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.write('void SomeIp_%s_OnConnect(uint16_t conId, boolean isConnected) {\n}\n\n' %
            (service['name']))
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('Std_ReturnType SomeIp_%s_OnRequest(uint32_t requestId, SomeIp_MessageType* req, SomeIp_MessageType* res) {\n' %
                (bName))
        if method.get('tp', False):
            C.write('  res->data = %sTpTxBuf;\n' % (bName))
        C.write('  memcpy(res->data, req->data, req->length);\n')
        C.write('  res->length = req->length;\n')
        C.write(
            '  ASLOG(%s, ("%s OnRequest %%X: len=%%d, data=[%%02X %%02X %%02X %%02X ...]\\n",\n' % (service['name'].upper(), method['name']))
        C.write(
            '    requestId, req->length, req->data[0], req->data[1], req->data[2], req->data[3]));\n')
        C.write('  return E_OK;\n')
        C.write('}\n\n')
        C.write(
            'Std_ReturnType SomeIp_%s_OnFireForgot(uint32_t requestId,SomeIp_MessageType* req) {\n' % (bName))
        C.write(
            '  ASLOG(%s, ("%s OnFireForgot %%X: len=%%d, data=[%%02X %%02X %%02X %%02X ...]\\n",\n' % (service['name'].upper(), method['name']))
        C.write(
            '    requestId, req->length, req->data[0], req->data[1], req->data[2], req->data[3]));\n')
        C.write('  return E_OK;\n')
        C.write('}\n\n')
        C.write(
            'Std_ReturnType SomeIp_%s_OnAsyncRequest(uint32_t requestId, SomeIp_MessageType* res) {\n' % (bName))
        C.write('  return E_OK;\n')
        C.write('}\n\n')
        if method.get('tp', False):
            Gen_MethodRxTxTp(C, service, method)
    for egroup in service['event-groups']:
        bName = '%s_%s' % (service['name'], egroup['name'])
        C.write(
            'void SomeIp_%s_OnSubscribe(boolean isSubscribe, TcpIp_SockAddrType* RemoteAddr) {\n' % (bName))
        C.write(
            '  ASLOG(%s, ("%s %%ssubscribed by %%d.%%d.%%d.%%d:%%d\\n", isSubscribe ? "" : "stop ",\n'
            '        RemoteAddr->addr[0], RemoteAddr->addr[1], RemoteAddr->addr[2], RemoteAddr->addr[3], RemoteAddr->port));\n'
            % (service['name'].upper(), egroup['name']))
        C.write('}\n\n')
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            if event.get('tp', False):
                Gen_DemoTxTp(C, beName)
            C.write(
                'Std_ReturnType %s_notify(uint8_t *data, uint32_t length) {\n' % (beName))
            C.write('  Std_ReturnType ercd = E_NOT_OK;\n')
            C.write('  static uint16_t sessionId = 0;\n')
            C.write(
                '  uint32_t requestId = ((uint32_t)SOMEIP_TX_EVT_%s << 16) + (++sessionId);\n' % (beName.upper()))
            if event.get('tp', False):
                C.write('  memcpy(%sTpTxBuf, data, length);\n' % (beName))
                C.write('  data = %sTpTxBuf;\n' % (beName))
                C.write('  length = 8000;\n')
            C.write('  ercd = SomeIp_Notification(requestId, data, length);\n')
            C.write('  return ercd;\n')
            C.write('}\n\n')
    C.close()
    C = open('%s/SS_%s.cpp' % (dir, service['name']), 'w')
    GenHeader(C)
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('extern "C" {\n')
    C.write('#include "SS_%s.h"\n' % (service['name']))
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('#include "Sd_Cfg.h"\n')
    C.write('}\n')
    C.write('#include "usomeip/usomeip.hpp"\n')
    C.write('#include "usomeip/server.hpp"\n')
    C.write('#include "Std_Debug.h"\n')
    C.write('#include <string.h>\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write('#define AS_LOG_%s 1\n' % (service['name'].upper()))
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.write('extern "C" {\n')
    C.write('void SomeIp_%s_OnConnect(uint16_t conId, boolean isConnected) {\n' %
            (service['name']))
    C.write('  as::usomeip::server::on_connect(SOMEIP_SSID_%s, conId, isConnected);\n' % (
            service['name'].upper()))
    C.write('}\n\n')
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('Std_ReturnType SomeIp_%s_OnRequest(uint32_t requestId, SomeIp_MessageType* req, SomeIp_MessageType* res) {\n' %
                (bName))
        C.write('  return as::usomeip::server::on_request(SOMEIP_RX_METHOD_%s, requestId, req, res);\n' % (
            bName.upper()))
        C.write('}\n\n')
        C.write(
            'Std_ReturnType SomeIp_%s_OnFireForgot(uint32_t requestId,SomeIp_MessageType* req) {\n' % (bName))
        C.write('  return as::usomeip::server::on_fire_forgot(SOMEIP_RX_METHOD_%s, requestId, req);\n' % (
            bName.upper()))
        C.write('}\n\n')
        C.write(
            'Std_ReturnType SomeIp_%s_OnAsyncRequest(uint32_t requestId, SomeIp_MessageType* res) {\n' % (bName))
        C.write('  return as::usomeip::server::on_async_request(SOMEIP_RX_METHOD_%s, requestId, res);\n' % (
            bName.upper()))
        C.write('}\n\n')
        if method.get('tp', False):
            C.write(
                'Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (bName))
            C.write('  return as::usomeip::server::on_method_tp_rx_data(SOMEIP_RX_METHOD_%s, requestId, msg);\n' % (
                bName.upper()))
            C.write('}\n\n')
            C.write(
                'Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (bName))
            C.write('  return as::usomeip::server::on_method_tp_tx_data(SOMEIP_RX_METHOD_%s, requestId, msg);\n' % (
                bName.upper()))
            C.write('}\n\n')

    for egroup in service['event-groups']:
        bName = '%s_%s' % (service['name'], egroup['name'])
        C.write(
            'void SomeIp_%s_OnSubscribe(boolean isSubscribe, TcpIp_SockAddrType* RemoteAddr) {\n' % (bName))
        C.write('return as::usomeip::server::on_subscribe(SD_EVENT_HANDLER_%s, isSubscribe, RemoteAddr);\n' % (
            bName.upper()))
        C.write('}\n\n')
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            if event.get('tp', False):
                C.write(
                    'Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (beName))
                C.write(
                    '  return as::usomeip::server::on_event_tp_tx_data(requestId, msg);\n')
                C.write('}\n\n')
    C.write('}\n')
    C.close()


def Gen_ClientServiceExCpp(service, dir):
    C = open('%s/CS_Ex%s.cpp' % (dir, service['name']), 'w')
    GenHeader(C)
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('#include "usomeip/usomeip.hpp"\n')
    C.write('#include "usomeip/client.hpp"\n')
    C.write('extern "C" {\n')
    C.write('#include "CS_%s.h"\n' % (service['name']))
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('#include "Sd_Cfg.h"\n')
    C.write('}\n')
    C.write('#include "plugin.h"\n')
    C.write('#include "Std_Timer.h"\n')
    C.write('using namespace as;\n')
    C.write('using namespace as::usomeip;\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write('class CS_%s;\n' % (service['name']))
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    C.write('static std::shared_ptr<CS_%s> CS_Instance = nullptr;\n' %
            (service['name']))
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.write('class CS_%s : public client::Client {\n' % (service['name']))
    C.write('public:\n')
    C.write('  CS_%s() {\n' % (service['name']))
    C.write('  }\n\n')
    C.write('  ~CS_%s() {\n' % (service['name']))
    C.write('  }\n\n')

    C.write('  void start() {\n')
    C.write('    identity(SOMEIP_CSID_%s);\n' % (service['name'].upper()))
    C.write('    require(SD_CLIENT_SERVICE_HANDLE_ID_%s);\n' % (service['name'].upper()))
    C.write('    m_BufferPool.create("CS_%s", 5, 1024 * 1024);\n' %
            (service['name']))
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('    bind(SOMEIP_TX_METHOD_%s, &m_BufferPool);\n' %
                (bName.upper()))
    for event_group in service['event-groups']:
        bName = '%s_%s' % (service['name'], event_group['name'])
        C.write('    subscribe(SD_CONSUMED_EVENT_GROUP_%s);\n' %
                (bName.upper()))
        for event in event_group['events']:
            beName = '%s_%s_%s' % (
                service['name'], event_group['name'], event['name'])
            C.write('    listen(SOMEIP_RX_EVT_%s, &m_BufferPool);\n' %
                    (beName.upper()))
    C.write('    Std_TimerStart(&m_Timer);\n')
    C.write('  }\n\n')

    C.write('  void stop() {\n')
    C.write('    Std_TimerStop(&m_Timer);\n')
    C.write('  }\n\n')

    C.write('  void onResponse(std::shared_ptr<Message> msg) {\n')
    C.write('    usLOG(INFO, "%s: on response: %%s\\n", msg->str().c_str());\n' %
            (service['name']))
    C.write('  }\n\n')
    C.write('  void onNotification(std::shared_ptr<Message> msg) {\n')
    C.write('    usLOG(INFO, "%s: on notification: %%s\\n", msg->str().c_str());\n' %
            (service['name']))
    C.write('  }\n\n')

    C.write('  void onError(std::shared_ptr<Message> msg) {\n')
    C.write('    usLOG(INFO, "%s: on error: %%s\\n", msg->str().c_str());\n' %
            (service['name']))
    C.write('  }\n\n')

    C.write('  void onAvailability(bool isAvailable) {\n')
    C.write('    usLOG(INFO, "%s: %%s\\n", isAvailable?"online":"offline");\n' % (
        service['name']))
    C.write('  }\n\n')

    C.write('  void run() {\n')
    C.write('    if (Std_GetTimerElapsedTime(&m_Timer) >= 1000000) {\n')
    C.write('      Std_TimerStart(&m_Timer);\n')
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('      uint32_t requestId =\n')
        C.write('        ((uint32_t)SOMEIP_TX_METHOD_%s << 16) + (++m_SessionId);\n' %
                (bName.upper()))
        C.write('      auto buffer = m_BufferPool.get();\n')
        C.write('      if (nullptr != buffer) {\n')
        C.write('        buffer->size = 5000;\n')
        C.write('        uint8_t *data = (uint8_t *)buffer->data;\n')
        C.write('        for (size_t i = 0; i < buffer->size; i++) {\n')
        C.write('          data[i] = m_SessionId + i;\n')
        C.write('        }\n')
        C.write('        request(requestId, buffer);\n')
        C.write('      }\n')

        break
    C.write('    }\n')
    C.write('  }\n\n')

    C.write('private:\n')
    C.write('  Std_TimerType m_Timer;\n')
    C.write('  BufferPool m_BufferPool;\n')
    C.write('  uint16_t m_SessionId = 0;\n')
    C.write('};\n\n')

    C.write('void CS_%s_init(void) {\n' % (service['name']))
    C.write('  CS_Instance = std::make_shared<CS_%s>();\n' % (service['name']))
    C.write('  CS_Instance->start();\n')
    C.write('}\n\n')

    C.write('void CS_%s_main(void) {\n' % (service['name']))
    C.write('  CS_Instance->run();\n')
    C.write('}\n\n')

    C.write('void CS_%s_deinit(void) {\n' % (service['name']))
    C.write('  CS_Instance->stop();\n')
    C.write('}\n\n')
    C.write('REGISTER_PLUGIN(CS_%s);\n' % (service['name']))


def Gen_ClientService(service, dir):
    H = open('%s/CS_%s.h' % (dir, service['name']), 'w')
    GenHeader(H)
    H.write('#ifndef _CS_%s_H\n' % (service['name'].upper()))
    H.write('#define _CS_%s_H\n' % (service['name'].upper()))
    H.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    H.write('#include "SomeIp.h"\n')
    H.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    H.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    H.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    H.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    H.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    H.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    H.write('void SomeIp_%s_OnAvailability(boolean isAvailable);\n' %
            (service['name']))
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        H.write('Std_ReturnType SomeIp_%s_OnResponse(uint32_t requestId, SomeIp_MessageType* res);\n' %
                (bName))
        H.write('Std_ReturnType SomeIp_%s_OnError(uint32_t requestId, Std_ReturnType ercd);\n' %
                (bName))
        if method.get('tp', False):
            H.write('Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg);\n' %
                    (bName))
            H.write('Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg);\n' %
                    (bName))
    for egroup in service['event-groups']:
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            H.write(
                'Std_ReturnType SomeIp_%s_OnNotification(uint32_t requestId, SomeIp_MessageType* evt);\n' % (beName))
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            if event.get('tp', False):
                H.write(
                    'Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg);\n' % (beName))
    H.write('#endif /* _CS_%s_H */\n' % (service['name'].upper()))
    H.close()
    C = open('%s/CS_%s.c' % (dir, service['name']), 'w')
    GenHeader(C)
    C.write('/* TODO: This is default demo code */\n')
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('#include "CS_%s.h"\n' % (service['name']))
    C.write('#include "Std_Debug.h"\n')
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('#include <string.h>\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write('#define AS_LOG_%s 1\n' % (service['name'].upper()))
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    C.write('static boolean lIsAvailable = FALSE;\n')
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        if method.get('tp', False):
            C.write('static uint8_t %sTpRxBuf[%d];\n' % (
                bName, method.get('tpRxSize', 1*1024*1024)))
            C.write('static uint8_t %sTpTxBuf[%d];\n' % (
                bName, method.get('tpTxSize', 1*1024*1024)))
    for egroup in service['event-groups']:
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            if event.get('tp', False):
                C.write('static uint8_t %sTpRxBuf[%d];\n' % (
                    beName, event.get('tpTxSize', 1*1024*1024)))
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.write('void SomeIp_%s_OnAvailability(boolean isAvailable) {\n' %
            (service['name']))
    C.write(
        '  ASLOG(%s, ("%%s\\n", isAvailable?"online":"offline"));\n' % (service['name'].upper()))
    C.write('  lIsAvailable = isAvailable;\n')
    C.write('}\n\n')
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('Std_ReturnType %s_request(uint8_t *data, uint32_t length) {\n' % (
            bName))
        C.write('  Std_ReturnType ercd = E_NOT_OK;\n')
        C.write('  static uint16_t sessionId = 0;\n')
        C.write('  uint32_t requestId = ((uint32_t)SOMEIP_TX_METHOD_%s << 16) | (++sessionId);\n' %
                (bName.upper()))
        if method.get('tp', False):
            C.write('  memcpy(%sTpTxBuf, data, length);\n' % (bName))
            C.write('  data = %sTpTxBuf;\n' % (bName))
            C.write('  length = 5000;\n')
        C.write('  if (lIsAvailable) {\n')
        C.write('    ASLOG(%s, ("%s Request %%X: len=%%d, data=[%%02X %%02X %%02X %%02X ...]\\n",\n' % (
            service['name'].upper(), method['name']))
        C.write(
            '          requestId, length, data[0], data[1], data[2], data[3]));\n')
        C.write('    ercd = SomeIp_Request(requestId, data, length);\n')
        C.write('  }\n')
        C.write('  return ercd;\n')
        C.write('}\n\n')
        C.write('Std_ReturnType SomeIp_%s_OnResponse(uint32_t requestId, SomeIp_MessageType* res) {\n' %
                (bName))
        C.write(
            '  ASLOG(%s, ("%s OnResponse %%X: len=%%d, data=[%%02X %%02X %%02X %%02X ...]\\n",\n' % (service['name'].upper(), method['name']))
        C.write(
            '        requestId, res->length, res->data[0], res->data[1], res->data[2], res->data[3]));\n')
        C.write('  return E_OK;\n')
        C.write('}\n\n')
        C.write('Std_ReturnType SomeIp_%s_OnError(uint32_t requestId, Std_ReturnType ercd) {\n' %
                (bName))
        C.write(
            '  ASLOG(%s, ("%s OnError %%X: %%d\\n", requestId, ercd));\n' % (service['name'].upper(), method['name']))
        C.write('  return E_OK;\n')
        C.write('}\n\n')
        if method.get('tp', False):
            Gen_MethodRxTxTp(C, service, method)
    for egroup in service['event-groups']:
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            C.write('Std_ReturnType SomeIp_%s_OnNotification(uint32_t requestId, SomeIp_MessageType* evt) {\n' % (
                beName
            ))
            C.write(
                '  ASLOG(%s, ("%s OnNotification %%X: len=%%d, data=[%%02X %%02X %%02X %%02X ...]\\n",\n' % (service['name'].upper(), event['name']))
            C.write(
                '        requestId, evt->length, evt->data[0], evt->data[1], evt->data[2], evt->data[3]));\n')
            C.write('  return E_OK;\n')
            C.write('}\n\n')
            if event.get('tp', False):
                Gen_DemoRxTp(C, beName)
    C.close()
    C = open('%s/CS_%s.cpp' % (dir, service['name']), 'w')
    GenHeader(C)
    C.write('/* TODO: This is default demo code */\n')
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('extern "C" {\n')
    C.write('#include "CS_%s.h"\n' % (service['name']))
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('}\n')
    C.write('#include "usomeip/usomeip.hpp"\n')
    C.write('#include "usomeip/client.hpp"\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.write('void SomeIp_%s_OnAvailability(boolean isAvailable) {\n' %
            (service['name']))
    C.write(
        '  as::usomeip::client::on_availability(SOMEIP_CSID_%s, isAvailable);\n' % (service['name'].upper()))
    C.write('}\n\n')
    for method in service.get('methods', []):
        bName = '%s_%s' % (service['name'], method['name'])
        C.write('Std_ReturnType SomeIp_%s_OnResponse(uint32_t requestId, SomeIp_MessageType* res) {\n' %
                (bName))
        C.write(
            '  return as::usomeip::client::on_response(SOMEIP_TX_METHOD_%s, requestId, res);\n' % (bName.upper()))
        C.write('}\n\n')
        C.write('Std_ReturnType SomeIp_%s_OnError(uint32_t requestId, Std_ReturnType ercd) {\n' %
                (bName))
        C.write(
            '  return as::usomeip::client::on_error(SOMEIP_TX_METHOD_%s, requestId, ercd);\n' % (bName.upper()))
        C.write('}\n\n')
        if method.get('tp', False):
            C.write(
                'Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (bName))
            C.write('  return as::usomeip::client::on_method_tp_rx_data(SOMEIP_TX_METHOD_%s, requestId, msg);\n' % (
                bName.upper()))
            C.write('}\n\n')
            C.write(
                'Std_ReturnType SomeIp_%s_OnTpCopyTxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (bName))
            C.write('  return as::usomeip::client::on_method_tp_tx_data(SOMEIP_TX_METHOD_%s, requestId, msg);\n' % (
                bName.upper()))
            C.write('}\n\n')
    for egroup in service['event-groups']:
        for event in egroup['events']:
            beName = '%s_%s_%s' % (
                service['name'], egroup['name'], event['name'])
            C.write('Std_ReturnType SomeIp_%s_OnNotification(uint32_t requestId, SomeIp_MessageType* evt) {\n' % (
                beName
            ))
            C.write('  return as::usomeip::client::on_notification(SOMEIP_RX_EVT_%s, requestId, evt);\n' % (
                beName.upper()))
            C.write('}\n\n')
            if event.get('tp', False):
                C.write(
                    'Std_ReturnType SomeIp_%s_OnTpCopyRxData(uint32_t requestId, SomeIp_TpMessageType *msg) {\n' % (beName))
                C.write('  return as::usomeip::client::on_event_tp_rx_data(SOMEIP_RX_EVT_%s, requestId, msg);\n' % (
                    beName.upper()))
                C.write('}\n\n')
    C.close()


def Gen_SD(cfg, dir):
    H = open('%s/Sd_Cfg.h' % (dir), 'w')
    GenHeader(H)
    H.write('#ifndef _SD_CFG_H\n')
    H.write('#define _SD_CFG_H\n')
    H.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    H.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    H.write('#define SD_RX_PID_MULTICAST 0\n')
    H.write('#define SD_RX_PID_UNICAST 0\n\n')
    for ID, service in enumerate(cfg.get('servers', [])):
        H.write('#define SD_SERVER_SERVICE_HANDLE_ID_%s %s\n' %
                (service['name'].upper(), ID))
    for ID, service in enumerate(cfg.get('clients', [])):
        H.write('#define SD_CLIENT_SERVICE_HANDLE_ID_%s %s\n' %
                (service['name'].upper(), ID))
    H.write('\n')
    ID = 0
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        for ge in service['event-groups']:
            H.write('#define SD_EVENT_HANDLER_%s_%s %s\n' %
                    (service['name'].upper(), ge['name'].upper(), ID))
            ID += 1
    ID = 0
    for service in cfg.get('clients', []):
        if 'event-groups' not in service:
            continue
        for ge in service['event-groups']:
            H.write('#define SD_CONSUMED_EVENT_GROUP_%s_%s %s\n' %
                    (service['name'].upper(), ge['name'].upper(), ID))
            ID += 1
    H.write('\n#define SD_MAIN_FUNCTION_PERIOD 10\n')
    H.write('#define SD_CONVERT_MS_TO_MAIN_CYCLES(x) \\\n')
    H.write('  ((x + SD_MAIN_FUNCTION_PERIOD - 1) / SD_MAIN_FUNCTION_PERIOD)\n')
    H.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    H.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    H.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    H.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    H.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    H.write('#endif /* _SD_CFG_H */\n')
    H.close()

    C = open('%s/Sd_Cfg.c' % (dir), 'w')
    GenHeader(C)
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('#include "Sd.h"\n')
    C.write('#include "Sd_Cfg.h"\n')
    C.write('#include "Sd_Priv.h"\n')
    C.write('#include "SoAd_Cfg.h"\n')
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    C.write(
        'boolean Sd_ServerService0_CRMC(PduIdType pduID, uint8_t type, uint16_t serviceID,\n')
    C.write('                               uint16_t instanceID, uint8_t majorVersion, uint32_t minorVersion,\n')
    C.write('                               const Sd_ConfigOptionStringType *receivedConfigOptionPtrArray,\n')
    C.write('                               const Sd_ConfigOptionStringType *configuredConfigOptionPtrArray);\n')
    for service in cfg.get('servers', []):
        for egroup in service['event-groups']:
            C.write('void SomeIp_%s_%s_OnSubscribe(boolean isSubscribe, TcpIp_SockAddrType* RemoteAddr);\n' % (
                service['name'], egroup['name']))
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    C.write('static Sd_ServerTimerType Sd_ServerTimerDefault = {\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(100),  /* InitialOfferDelayMax */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(10),   /* InitialOfferDelayMin */\n')
    C.write(
        '  SD_CONVERT_MS_TO_MAIN_CYCLES(200),  /* InitialOfferRepetitionBaseDelay */\n')
    C.write('  3,                                  /* InitialOfferRepetitionsMax */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(3000), /* OfferCyclicDelay */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(1500), /* RequestResponseMaxDelay */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(0),    /* RequestResponseMinDelay */\n')
    C.write('  5, /* TTL seconds */\n')
    C.write('};\n\n')

    C.write('static Sd_ClientTimerType Sd_ClientTimerDefault = {\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(100),  /* InitialFindDelayMax */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(10),   /* InitialFindDelayMin */\n')
    C.write(
        '  SD_CONVERT_MS_TO_MAIN_CYCLES(200),  /* InitialFindRepetitionsBaseDelay */\n')
    C.write('  3,                                  /* InitialFindRepetitionsMax */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(1500), /* RequestResponseMaxDelay */\n')
    C.write('  SD_CONVERT_MS_TO_MAIN_CYCLES(0),    /* RequestResponseMinDelay */\n')
    C.write('  5, /* TTL seconds */\n')
    C.write('};\n\n')
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        C.write('static Sd_EventHandlerContextType Sd_EventHandlerContext_%s[%d];\n' % (
            service['name'], len(service['event-groups'])))
        for ge in service['event-groups']:
            C.write('static Sd_EventHandlerSubscriberType Sd_EventHandlerSubscriber_%s_%s[3];\n' % (
                service['name'], ge['name']))
        C.write('static const Sd_EventHandlerType Sd_EventHandlers_%s[] = {\n' % (
            service['name']))
        for ID, ge in enumerate(service['event-groups']):
            C.write('  {\n')
            C.write('    SD_EVENT_HANDLER_%s_%s, /* HandleId */\n' %
                    (service['name'].upper(), ge['name'].upper()))
            C.write('    %s, /* EventGroupId */\n' % (ge['groupId']))
            C.write('    0, /* MulticastThreshold */\n')
            C.write('    &Sd_EventHandlerContext_%s[%d],\n' % (
                service['name'], ID))
            C.write('    Sd_EventHandlerSubscriber_%s_%s,\n' % (
                service['name'], ge['name']))
            C.write('    ARRAY_SIZE(Sd_EventHandlerSubscriber_%s_%s),\n' % (
                service['name'], ge['name']))
            C.write('   SomeIp_%s_%s_OnSubscribe,\n' %
                    (service['name'], ge['name']))
            C.write('  },\n')
        C.write('};\n\n')
    for service in cfg.get('clients', []):
        if 'event-groups' not in service:
            continue
        C.write('static Sd_ConsumedEventGroupContextType Sd_ConsumedEventGroupContext_%s[%d];\n' % (
            service['name'], len(service['event-groups'])))
        C.write('static const Sd_ConsumedEventGroupType Sd_ConsumedEventGroups_%s[] = {\n' % (
            service['name']))
        for ID, ge in enumerate(service['event-groups']):
            C.write('  {\n')
            C.write('    FALSE, /* AutoRequire */\n')
            C.write('    SD_CONSUMED_EVENT_GROUP_%s_%s, /* HandleId */\n' %
                    (service['name'].upper(), ge['name'].upper()))
            C.write('    %s, /* EventGroupId */\n' % (ge['groupId']))
            C.write('    &Sd_ConsumedEventGroupContext_%s[%d],\n' % (
                service['name'], ID))
            C.write('  },\n')
        C.write('};\n\n')
    C.write('static Sd_ServerServiceContextType Sd_ServerService_Contexts[%s];\n\n' % (
        len(cfg.get('servers', []))))
    C.write('static const Sd_ServerServiceType Sd_ServerServices[] = {\n')
    for ID, service in enumerate(cfg.get('servers', [])):
        C.write('  {\n')
        C.write('    FALSE,                           /* AutoAvailable */\n')
        C.write('    SD_SERVER_SERVICE_HANDLE_ID_%s,  /* HandleId */\n' %
                (service['name'].upper()))
        C.write('    %s,                         /* ServiceId */\n' %
                (service['service']))
        C.write('    %s,                         /* InstanceId */\n' %
                (service['instance']))
        C.write('    0,                              /* MajorVersion */\n')
        C.write('    0,                              /* MinorVersion */\n')
        if ('unreliable' in service):
            C.write('    SOAD_SOCKID_SOMEIP_%s,     /* SoConId */\n' %
                    (service['name'].upper()))
            C.write('    TCPIP_IPPROTO_UDP,              /* ProtocolType */\n')
        else:
            C.write('    SOAD_SOCKID_SOMEIP_%s_SERVER,     /* SoConId */\n' %
                    (service['name'].upper()))
            C.write('    TCPIP_IPPROTO_TCP,              /* ProtocolType */\n')
        C.write(
            '    Sd_ServerService0_CRMC,         /* CapabilityRecordMatchCalloutRef */\n')
        C.write('    &Sd_ServerTimerDefault,\n')
        C.write('    &Sd_ServerService_Contexts[%s],\n' % (ID))
        C.write('    0, /* InstanceIndex */\n')
        if 'event-groups' not in service:
            C.write('    NULL,\n    0,\n')
        else:
            C.write('    Sd_EventHandlers_%s,\n' % (service['name']))
            C.write('    ARRAY_SIZE(Sd_EventHandlers_%s),\n' %
                    (service['name']))
        C.write('  },\n')
    C.write('};\n\n')
    C.write('static Sd_ClientServiceContextType Sd_ClientService_Contexts[%s];\n\n' % (
        len(cfg.get('clients', []))))
    C.write('static const Sd_ClientServiceType Sd_ClientServices[] = {\n')
    for ID, service in enumerate(cfg.get('clients', [])):
        C.write('  {\n')
        C.write('    FALSE,                           /* AutoRequire */\n')
        C.write('    SD_CLIENT_SERVICE_HANDLE_ID_%s,  /* HandleId */\n' %
                (service['name'].upper()))
        C.write('    %s,                         /* ServiceId */\n' %
                (service['service']))
        C.write('    %s,                         /* InstanceId */\n' %
                (service['instance']))
        C.write('    0,                              /* MajorVersion */\n')
        C.write('    0,                              /* MinorVersion */\n')
        C.write('    SOAD_SOCKID_SOMEIP_%s, /* SoConId */\n' %
                (service['name'].upper()))
        if ('unreliable' in service):
            C.write('    TCPIP_IPPROTO_UDP,              /* ProtocolType */\n')
        else:
            C.write('    TCPIP_IPPROTO_TCP,              /* ProtocolType */\n')
        C.write(
            '    NULL,                           /* CapabilityRecordMatchCalloutRef */\n')
        C.write('    &Sd_ClientTimerDefault,\n')
        C.write('    &Sd_ClientService_Contexts[%s],\n' % (ID))
        C.write('    0, /* InstanceIndex */\n')
        if 'event-groups' not in service:
            C.write('    NULL,\n    0,\n')
        else:
            C.write('    Sd_ConsumedEventGroups_%s,\n' % (service['name']))
            C.write('    ARRAY_SIZE(Sd_ConsumedEventGroups_%s),\n' %
                    (service['name']))
        C.write('  },\n')
    C.write('};\n\n')
    C.write('static uint8_t sd_buffer[1400];\n')
    C.write('static Sd_InstanceContextType sd_context;\n')
    C.write('static const Sd_InstanceType Sd_Instances[] = {\n')
    C.write('  {\n')
    C.write('    "%s",                             /* Hostname */\n' %
            (cfg['SD']['hostname']))
    C.write(
        '    SD_CONVERT_MS_TO_MAIN_CYCLES(1000), /* SubscribeEventgroupRetryDelay */\n')
    C.write(
        '    3,                                  /* SubscribeEventgroupRetryMax */\n')
    C.write('    {\n')
    C.write('      SD_RX_PID_MULTICAST,      /* RxPduId */\n')
    C.write('      SOAD_SOCKID_SD_MULTICAST, /* SoConId */\n')
    C.write('    },                          /* MulticastRxPdu */\n')
    C.write('    {\n')
    C.write('      SD_RX_PID_UNICAST,      /* RxPduId */\n')
    C.write('      SOAD_SOCKID_SD_UNICAST, /* SoConId */\n')
    C.write('    },                        /* UnicastRxPdu */\n')
    C.write('    {\n')
    C.write('      SOAD_TX_PID_SD_MULTICAST,    /* MulticastTxPduId */\n')
    C.write('      SOAD_TX_PID_SD_UNICAST,      /* UnicastTxPduId */\n')
    C.write('    },                             /* TxPdu */\n')
    C.write('    Sd_ServerServices,             /* ServerServices */\n')
    C.write('    ARRAY_SIZE(Sd_ServerServices), /* numOfServerServices */\n')
    C.write('    Sd_ClientServices,             /* ClientServices */\n')
    C.write('    ARRAY_SIZE(Sd_ClientServices), /* numOfClientServices */\n')
    C.write('    sd_buffer,                     /*buffer */\n')
    C.write('    sizeof(sd_buffer),\n')
    C.write('    &sd_context,\n')
    C.write('  },\n')
    C.write('};\n\n')
    C.write('static const Sd_ServerServiceType* Sd_ServerServicesMap[] = {\n')
    for ID, service in enumerate(cfg.get('servers', [])):
        C.write('  &Sd_ServerServices[%s],\n' % (ID))
    C.write('};\n\n')
    C.write('static const Sd_ClientServiceType* Sd_ClientServicesMap[] = {\n')
    for ID, service in enumerate(cfg.get('clients', [])):
        C.write('  &Sd_ClientServices[%s],\n' % (ID))
    C.write('};\n\n')
    C.write('static const uint16_t Sd_EventHandlersMap[] = {\n')
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        for ge in service['event-groups']:
            C.write('  SD_SERVER_SERVICE_HANDLE_ID_%s,\n' %
                    (service['name'].upper()))
    C.write('  -1,\n};\n\n')
    C.write(
        'static const uint16_t Sd_PerServiceEventHandlerMap[] = {\n')
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        for id, ge in enumerate(service['event-groups']):
            C.write('  %s,\n' % (id))
    C.write('  -1,\n};\n\n')
    C.write('static const uint16_t Sd_ConsumedEventGroupsMap[] = {\n')
    for service in cfg.get('clients', []):
        if 'event-groups' not in service:
            continue
        for ge in service['event-groups']:
            C.write('  SD_CLIENT_SERVICE_HANDLE_ID_%s,\n' %
                    (service['name'].upper()))
    C.write('  -1,\n};\n\n')
    C.write(
        'static const uint16_t Sd_PerServiceConsumedEventGroupsMap[] = {\n')
    for service in cfg.get('clients', []):
        if 'event-groups' not in service:
            continue
        for id, ge in enumerate(service['event-groups']):
            C.write('  %s,\n' % (id))
    C.write('  -1,\n};\n\n')
    C.write('const Sd_ConfigType Sd_Config = {\n')
    C.write('  Sd_Instances,\n')
    C.write('  ARRAY_SIZE(Sd_Instances),\n')
    C.write('  Sd_ServerServicesMap,\n')
    C.write('  ARRAY_SIZE(Sd_ServerServicesMap),\n')
    C.write('  Sd_ClientServicesMap,\n')
    C.write('  ARRAY_SIZE(Sd_ClientServicesMap),\n')
    C.write('  Sd_EventHandlersMap,\n')
    C.write('  Sd_PerServiceEventHandlerMap,\n')
    C.write('  ARRAY_SIZE(Sd_EventHandlersMap)-1,\n')
    C.write('  Sd_ConsumedEventGroupsMap,\n')
    C.write('  Sd_PerServiceConsumedEventGroupsMap,\n')
    C.write('  ARRAY_SIZE(Sd_ConsumedEventGroupsMap)-1,\n')
    C.write('};\n')
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.close()


def Gen_SOMEIP(cfg, dir):
    H = open('%s/SomeIp_Cfg.h' % (dir), 'w')
    GenHeader(H)
    H.write('#ifndef _SOMEIP_CFG_H\n')
    H.write('#define _SOMEIP_CFG_H\n')
    H.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    H.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    ID = 0
    for service in cfg.get('servers', []):
        H.write('#define SOMEIP_SSID_%s %s\n' % (service['name'].upper(), ID))
        ID += 1
    for service in cfg.get('clients', []):
        H.write('#define SOMEIP_CSID_%s %s\n' % (service['name'].upper(), ID))
        ID += 1
    H.write('\n')
    ID = 0
    for service in cfg.get('servers', []):
        if 'reliable' in service:
            listen = service['listen'] if 'listen' in service else 3
            for i in range(listen):
                H.write('#define SOMEIP_RX_PID_SOMEIP_%s%s %s\n' %
                        (service['name'].upper(), i, ID))
                H.write('#define SOMEIP_TX_PID_SOMEIP_%s%s %s\n' %
                        (service['name'].upper(), i, ID))
                ID += 1
        else:
            H.write('#define SOMEIP_RX_PID_SOMEIP_%s %s\n' %
                    (service['name'].upper(), ID))
            H.write('#define SOMEIP_TX_PID_SOMEIP_%s %s\n' %
                    (service['name'].upper(), ID))
            ID += 1
    for service in cfg.get('clients', []):
        H.write('#define SOMEIP_RX_PID_SOMEIP_%s %s\n' %
                (service['name'].upper(), ID))
        H.write('#define SOMEIP_TX_PID_SOMEIP_%s %s\n' %
                (service['name'].upper(), ID))
        ID += 1
    H.write('\n')
    ID = 0
    for service in cfg.get('servers', []):
        if 'methods' not in service:
            continue
        for method in service.get('methods', []):
            bName = '%s_%s' % (service['name'], method['name'])
            H.write('#define SOMEIP_RX_METHOD_%s %s\n' % (bName.upper(), ID))
    H.write('\n')
    ID = 0
    for service in cfg.get('clients', []):
        if 'methods' not in service:
            continue
        for method in service.get('methods', []):
            bName = '%s_%s' % (service['name'], method['name'])
            H.write('#define SOMEIP_TX_METHOD_%s %s\n' % (bName.upper(), ID))
    H.write('\n')
    ID = 0
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        for egroup in service['event-groups']:
            for event in egroup['events']:
                beName = '%s_%s_%s' % (
                    service['name'],  egroup['name'], event['name'])
                H.write('#define SOMEIP_TX_EVT_%s %s\n' % (beName.upper(), ID))
                ID += 1
    H.write('\n')
    ID = 0
    for service in cfg.get('clients', []):
        if 'event-groups' not in service:
            continue
        for egroup in service['event-groups']:
            for event in egroup['events']:
                beName = '%s_%s_%s' % (
                    service['name'],  egroup['name'], event['name'])
                H.write('#define SOMEIP_RX_EVT_%s %s\n' % (beName.upper(), ID))
                ID += 1
    H.write('\n#define SOMEIP_MAIN_FUNCTION_PERIOD 10\n')
    H.write('#define SOMEIP_CONVERT_MS_TO_MAIN_CYCLES(x) \\\n')
    H.write('  ((x + SOMEIP_MAIN_FUNCTION_PERIOD - 1) / SOMEIP_MAIN_FUNCTION_PERIOD)\n')
    H.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    H.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    H.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    H.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    H.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    H.write('#endif /* _SOMEIP_CFG_H */\n')
    H.close()

    C = open('%s/SomeIp_Cfg.c' % (dir), 'w')
    GenHeader(C)
    C.write(
        '/* ================================ [ INCLUDES  ] ============================================== */\n')
    C.write('#include "SomeIp.h"\n')
    C.write('#include "SomeIp_Cfg.h"\n')
    C.write('#include "SomeIp_Priv.h"\n')
    C.write('#include "SoAd_Cfg.h"\n')
    C.write('#include "Sd_Cfg.h"\n')
    for service in cfg.get('servers', []):
        C.write('#include "SS_%s.h"\n' % (service['name']))
    for service in cfg.get('clients', []):
        C.write('#include "CS_%s.h"\n' % (service['name']))
    C.write(
        '/* ================================ [ MACROS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ TYPES     ] ============================================== */\n')
    C.write(
        '/* ================================ [ DECLARES  ] ============================================== */\n')
    for service in cfg.get('servers', []):
        Gen_ServerService(service, dir)
        Gen_ServerServiceExCpp(service, dir)
    for service in cfg.get('clients', []):
        Gen_ClientService(service, dir)
        Gen_ClientServiceExCpp(service, dir)
    C.write(
        '/* ================================ [ DATAS     ] ============================================== */\n')
    for service in cfg.get('servers', []):
        if 'methods' not in service:
            continue
        C.write('static const SomeIp_ServerMethodType someIpServerMethods_%s[] = {\n' % (
            service['name']))
        for method in service.get('methods', []):
            bName = '%s_%s' % (service['name'],  method['name'])
            C.write('  {\n')
            C.write('    %s, /* Method ID */\n' % (method['methodId']))
            C.write('    %s, /* interface version */\n' % (method['version']))
            C.write('    SomeIp_%s_OnRequest,\n' % (bName))
            C.write('    SomeIp_%s_OnFireForgot,\n' % (bName))
            C.write('    SomeIp_%s_OnAsyncRequest,\n' % (bName))
            if method.get('tp', False):
                C.write('    SomeIp_%s_OnTpCopyRxData,\n' % (bName))
                C.write('    SomeIp_%s_OnTpCopyTxData,\n' % (bName))
            else:
                C.write('    NULL,\n')
                C.write('    NULL,\n')
            resMaxLen = method.get('resMaxLen', 512)
            if method.get('tp', False):
                resMaxLen = 1404
            C.write('    %s /* resMaxLen */\n' % (resMaxLen))
            C.write('  },\n')
        C.write("};\n\n")
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        C.write('static const SomeIp_ServerEventType someIpServerEvents_%s[] = {\n' % (
            service['name']))
        for egroup in service['event-groups']:
            for event in egroup['events']:
                bName = '%s_%s' % (service['name'],  egroup['name'])
                beName = '%s_%s' % (bName, event['name'])
                C.write('  {\n')
                C.write(
                    '    SD_EVENT_HANDLER_%s, /* SD EventGroup Handle ID */\n' % (bName.upper()))
                C.write('    %s, /* Event ID */\n' % (event['eventId']))
                C.write('    %s, /* interface version */\n' %
                        (event['version']))
                if event.get('tp', False):
                    C.write('    SomeIp_%s_OnTpCopyTxData,\n' % (beName))
                else:
                    C.write('  NULL,\n')
                C.write('  },\n')
        C.write("};\n\n")
    for service in cfg.get('clients', []):
        if 'methods' not in service:
            continue
        C.write('static const SomeIp_ClientMethodType someIpClientMethods_%s[] = {\n' % (
            service['name']))
        for method in service.get('methods', []):
            bName = '%s_%s' % (service['name'],  method['name'])
            C.write('  {\n')
            C.write('    %s, /* Method ID */\n' % (method['methodId']))
            C.write('    %s, /* interface version */\n' % (method['version']))
            C.write('    SomeIp_%s_OnResponse,\n' % (bName))
            C.write('    SomeIp_%s_OnError,\n' % (bName))
            if method.get('tp', False):
                C.write('    SomeIp_%s_OnTpCopyRxData,\n' % (bName))
                C.write('    SomeIp_%s_OnTpCopyTxData,\n' % (bName))
            else:
                C.write('    NULL,\n')
                C.write('    NULL,\n')
            C.write('  },\n')
        C.write("};\n\n")
    for service in cfg.get('clients', []):
        if 'event-groups' not in service:
            continue
        C.write('static const SomeIp_ClientEventType someIpClientEvents_%s[] = {\n' % (
            service['name']))
        for egroup in service['event-groups']:
            for event in egroup['events']:
                beName = '%s_%s_%s' % (
                    service['name'],  egroup['name'], event['name'])
                C.write('  {\n')
                C.write('    %s, /* Event ID */\n' % (event['eventId']))
                C.write('    %s, /* interface version */\n' %
                        (event['version']))
                C.write('    SomeIp_%s_OnNotification,\n' % (beName))
                if event.get('tp', False):
                    C.write('    SomeIp_%s_OnTpCopyRxData,\n' % (beName))
                else:
                    C.write('  NULL,\n')
                C.write('  },\n')
        C.write("};\n\n")
    for service in cfg.get('servers', []):
        if 'reliable' in service:
            numOfConnections = service['listen'] if 'listen' in service else 3
            C.write('static SomeIp_TcpBufferType someIpTcpBuffer_%s[%s];\n\n' % (
                service['name'], numOfConnections))
        else:
            numOfConnections = 1
        C.write('static SomeIp_ServerContextType someIpServerContext_%s;\n\n' % (
            service['name']))
        C.write('static SomeIp_ServerConnectionContextType someIpServerConnectionContext_%s[%s];\n\n' % (
            service['name'], numOfConnections))
        C.write('static const SomeIp_ServerConnectionType someIpServerServiceConnections_%s[%s] = {\n' % (
            service['name'], numOfConnections))
        for i in range(numOfConnections):
            C.write('  {\n')
            C.write('    &someIpServerConnectionContext_%s[%s],\n' %
                    (service['name'], i))
            if 'reliable' in service:
                C.write('    SOAD_TX_PID_SOMEIP_%s_APT%s,\n' %
                        (service['name'].upper(), i))
                C.write('    SOAD_SOCKID_SOMEIP_%s_APT%s,\n' %
                        (service['name'].upper(), i))
                C.write('    &someIpTcpBuffer_%s[%s],\n' % (
                    service['name'], i))
            else:
                C.write('    SOAD_TX_PID_SOMEIP_%s,\n' %
                        (service['name'].upper()))
                C.write('    SOAD_SOCKID_SOMEIP_%s,\n' %
                        (service['name'].upper()))
                C.write('    NULL\n')
            C.write('  },\n')
        C.write('};\n\n')
        C.write('static const SomeIp_ServerServiceType someIpServerService_%s = {\n' % (
            service['name']))
        C.write('  %s, /* serviceId */\n' % (service['service']))
        C.write('  %s, /* clientId */\n' % (service['clientId']))
        if 'methods' not in service:
            C.write('  NULL,\n  0,\n')
        else:
            C.write('  someIpServerMethods_%s,\n' % (service['name']))
            C.write('  ARRAY_SIZE(someIpServerMethods_%s),\n' %
                    (service['name']))
        if 'event-groups' not in service:
            C.write('  NULL,\n  0,\n')
        else:
            C.write('  someIpServerEvents_%s,\n' % (service['name']))
            C.write('  ARRAY_SIZE(someIpServerEvents_%s),\n' %
                    (service['name']))
        C.write('  someIpServerServiceConnections_%s,\n' % (service['name']))
        C.write('  ARRAY_SIZE(someIpServerServiceConnections_%s),\n' %
                (service['name']))
        if 'reliable' in service:
            C.write('  TCPIP_IPPROTO_TCP,\n')
        else:
            C.write('  TCPIP_IPPROTO_UDP,\n')
        C.write('  &someIpServerContext_%s,\n' % (service['name']))
        C.write('  SOMEIP_CONVERT_MS_TO_MAIN_CYCLES(%s),\n' %
                (service.get('SeparationTime', 10)))
        C.write('  SomeIp_%s_OnConnect,\n' % (service['name']))
        C.write('};\n\n')
    for service in cfg.get('clients', []):
        if 'reliable' in service:
            C.write('static SomeIp_TcpBufferType someIpTcpBuffer_%s;\n\n' % (
                    service['name']))
        C.write('static SomeIp_ClientServiceContextType someIpClientServiceContext_%s;\n' % (
            service['name']))
        C.write('static const SomeIp_ClientServiceType someIpClientService_%s = {\n' % (
            service['name']))
        C.write('  %s, /* serviceId */\n' % (service['service']))
        C.write('  %s, /* clientId */\n' % (service['clientId']))
        C.write('  SD_CLIENT_SERVICE_HANDLE_ID_%s, /* sdHandleID */\n' %
                (service['name'].upper()))
        if 'methods' not in service:
            C.write('  NULL,\n  0,\n')
        else:
            C.write('  someIpClientMethods_%s,\n' % (service['name']))
            C.write('  ARRAY_SIZE(someIpClientMethods_%s),\n' %
                    (service['name']))
        if 'event-groups' not in service:
            C.write('  NULL,\n  0,\n')
        else:
            C.write('  someIpClientEvents_%s,\n' % (service['name']))
            C.write('  ARRAY_SIZE(someIpClientEvents_%s),\n' %
                    (service['name']))
        C.write('  &someIpClientServiceContext_%s,\n' %
                (service['name']))
        C.write('  SOAD_TX_PID_SOMEIP_%s,\n' % (service['name'].upper()))
        C.write('  SomeIp_%s_OnAvailability,\n' % (service['name']))
        if 'reliable' in service:
            C.write('  &someIpTcpBuffer_%s,\n' % (service['name']))
        else:
            C.write('  NULL,\n')
        C.write('  SOMEIP_CONVERT_MS_TO_MAIN_CYCLES(%s),\n' %
                (service.get('SeparationTime', 10)))
        C.write('  SOMEIP_CONVERT_MS_TO_MAIN_CYCLES(%s),\n' %
                (service.get('ResponseTimeout', 1000)))
        C.write('};\n\n')
    C.write('static const SomeIp_ServiceType SomeIp_Services[] = {\n')
    for service in cfg.get('servers', []):
        C.write('  {\n')
        C.write('    TRUE,\n')
        if 'reliable' in service:
            C.write('    SOAD_SOCKID_SOMEIP_%s_SERVER,\n' %
                    (service['name'].upper()))
        else:
            C.write('    SOAD_SOCKID_SOMEIP_%s,\n' % (service['name'].upper()))
        C.write('    &someIpServerService_%s,\n' % (service['name']))
        C.write('  },\n')
    for service in cfg.get('clients', []):
        C.write('  {\n')
        C.write('    FALSE,\n')
        C.write('    SOAD_SOCKID_SOMEIP_%s,\n' % (service['name'].upper()))
        C.write('    &someIpClientService_%s,\n' % (service['name']))
        C.write('  },\n')
    C.write('};\n\n')
    C.write('static const uint16_t Sd_PID2ServiceMap[] = {\n')
    for service in cfg.get('servers', []):
        if 'reliable' in service:
            numOfConnections = service['listen'] if 'listen' in service else 3
        else:
            numOfConnections = 1
        for i in range(numOfConnections):
            C.write('  SOMEIP_SSID_%s,\n' % (service['name'].upper()))
    for service in cfg.get('clients', []):
        C.write('  SOMEIP_CSID_%s,\n' % (service['name'].upper()))
    C.write('};\n\n')
    C.write('static const uint16_t Sd_PID2ServiceConnectionMap[] = {\n')
    for service in cfg.get('servers', []):
        if 'reliable' in service:
            numOfConnections = service['listen'] if 'listen' in service else 3
        else:
            numOfConnections = 1
        for i in range(numOfConnections):
            C.write('  %s,\n' % (i))
    for service in cfg.get('clients', []):
        C.write('  0,\n')
    C.write('};\n\n')
    C.write('static const uint16_t Sd_TxMethod2ServiceMap[] = {\n')
    for service in cfg.get('clients', []):
        if 'methods' not in service:
            continue
        for method in service.get('methods', []):
            C.write('  SOMEIP_CSID_%s,/* %s */\n' %
                    (service['name'].upper(), method['name']))
    C.write('  -1\n};\n\n')
    C.write('static const uint16_t Sd_TxMethod2PerServiceMap[] = {\n')
    for service in cfg.get('clients', []):
        if 'methods' not in service:
            continue
        for i, method in enumerate(service.get('methods', [])):
            C.write('  %s, /* %s */\n' % (i, method['name']))
    C.write('  -1\n};\n\n')
    C.write('static const uint16_t Sd_TxEvent2ServiceMap[] = {\n')
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        for egroup in service['event-groups']:
            for event in egroup['events']:
                C.write('  SOMEIP_SSID_%s, /* %s %s */\n' %
                        (service['name'].upper(), egroup['name'], event['name']))
    C.write('  -1\n};\n\n')
    C.write('static const uint16_t Sd_TxEvent2PerServiceMap[] = {\n')
    for service in cfg.get('servers', []):
        if 'event-groups' not in service:
            continue
        ID = 0
        for egroup in service['event-groups']:
            for event in egroup['events']:
                C.write('  %s, /* %s %s */\n' %
                        (ID, egroup['name'], event['name']))
                ID += 1
    C.write('  -1\n};\n\n')
    C.write('const SomeIp_ConfigType SomeIp_Config = {\n')
    C.write('  SOMEIP_CONVERT_MS_TO_MAIN_CYCLES(%s),\n' %
            (cfg.get('TpRxTimeoutTime', 200)))
    C.write('  SomeIp_Services,\n')
    C.write('  ARRAY_SIZE(SomeIp_Services),\n')
    C.write('  Sd_PID2ServiceMap,\n')
    C.write('  Sd_PID2ServiceConnectionMap,\n')
    C.write('  ARRAY_SIZE(Sd_PID2ServiceMap),\n')
    C.write('  Sd_TxMethod2ServiceMap,\n')
    C.write('  Sd_TxMethod2PerServiceMap,\n')
    C.write('  ARRAY_SIZE(Sd_TxMethod2ServiceMap)-1,\n')
    C.write('  Sd_TxEvent2ServiceMap,\n')
    C.write('  Sd_TxEvent2PerServiceMap,\n')
    C.write('  ARRAY_SIZE(Sd_TxEvent2ServiceMap)-1,\n')
    C.write('};\n\n')
    C.write(
        '/* ================================ [ LOCALS    ] ============================================== */\n')
    C.write(
        '/* ================================ [ FUNCTIONS ] ============================================== */\n')
    C.close()


def Gen_SomeIp(cfg, dir):
    Gen_SD(cfg, dir)
    Gen_SOMEIP(cfg, dir)
