#ifndef HTTP_REQUESTS_H
#include <stdio.h>
#include <stdlib.h>
#include <zephyr/net/socket.h>

void nslookup(const char * hostname, struct zsock_addrinfo **results);
void PrintAddrInfoResults(struct zsock_addrinfo **results);
void HTTPGet(int sock, char * hostname, char * url);
void HTTPPut(int sock, char * hostname, char * url);
void HTTPDelete(int sock, char * hostname, char * url);

int ConnectSocket(struct zsock_addrinfo **results, uint16_t port);

#endif // !HTTP_REQUESTS_H

