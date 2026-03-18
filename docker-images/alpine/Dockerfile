FROM alpine:latest
RUN apk add openssh-server
RUN mkdir /var/run/sshd
RUN ssh-keygen -A
RUN echo 'root:password' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]