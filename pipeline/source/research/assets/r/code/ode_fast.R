# Algebraic grouping of the original R equations. No physiological values are
# introduced here; every coefficient comes from create.params in the original model.
build_transport_matrix <- function(p) {
  states <- names(create.inits(p))
  M <- matrix(0,14,14,dimnames=list(states,states))
  M['APlas','APlas'] <- -p$QCP*p$Free/p$VPlas
  for(x in list(c('AF','QF','VF','PF'),c('AL','QL','VL','PL'),c('AR','QR','VR','PR'),
                c('AK','QK','VK','PK'),c('AB','QB','VB','PB'),c('ABm','QBm','VBm','PBm'),c('ALu','QLu','VLu','PLu'))) {
    flow <- p[[x[2]]];if(x[1]=='AL')flow <- p$QL+p$QG
    M['APlas',x[1]] <- flow*p$Free/(p[[x[3]]]*p[[x[4]]])
  }
  for(x in list(c('AG','QG','VG','PG'),c('AF','QF','VF','PF'),c('ALu','QLu','VLu','PLu'),
                c('AB','QB','VB','PB'),c('ABm','QBm','VBm','PBm'),c('AK','QK','VK','PK'),c('AR','QR','VR','PR'))) {
    M[x[1],'APlas'] <- p[[x[2]]]*p$Free/p$VPlas
    M[x[1],x[1]] <- -p[[x[2]]]*p$Free/(p[[x[3]]]*p[[x[4]]])
  }
  M['AL','APlas'] <- p$QL*p$Free/p$VPlas
  M['AL','AG'] <- p$QG*p$Free/(p$VG*p$PG)
  M['AL','AL'] <- -(p$QL+p$QG)*p$Free/(p$VL*p$PL)
  M['AFil','APlas'] <- p$QFil*p$Free/p$VPlas
  M['AFil','AFil'] <- -p$QFil/p$VFil
  M['AStor','AFil'] <- p$QFil/p$VFil
  M['AStor','AStor'] <- -p$kurine
  M['AUrine','AStor'] <- p$kurine
  stopifnot(max(abs(colSums(M[1:12,,drop=FALSE])))<1e-10)
  M
}
ode.fast <- function(time,inits,params) {
  d <- drop(params$transport_matrix %*% inits)
  cf <- inits[9]/params$VFil
  reabs <- params$Tm*cf/(params$Kt+cf)
  available <- params$f_water*inits[13]+params$f_aqua*params$Intake_aquatic+params$f_terri*params$Intake_terrestrial
  d[2] <- d[2]+available
  d[8] <- d[8]+reabs
  d[9] <- d[9]-reabs
  d[14] <- available
  list(d,c(CPlas=unname(inits[1]/params$VPlas),Mass_Balance=unname(inits[14]-sum(inits[1:12]))))
}
