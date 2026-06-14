FROM jenkins/jenkins:lts-jdk21

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

COPY setup.groovy /usr/share/jenkins/ref/init.groovy.d/setup.groovy
