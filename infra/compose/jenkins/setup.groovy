import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import java.util.UUID
import jenkins.model.Jenkins

def instance = Jenkins.getInstance()
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
def adminPassword = System.getenv("JENKINS_ADMIN_PASSWORD") ?: UUID.randomUUID().toString()
hudsonRealm.createAccount("admin", adminPassword)
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)
instance.save()

println("Jenkins setup completed successfully.")
