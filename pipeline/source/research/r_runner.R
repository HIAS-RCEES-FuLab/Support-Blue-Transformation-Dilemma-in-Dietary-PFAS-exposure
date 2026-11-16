# US 2003-2016 longitudinal PFOA/PFOS runner for the adapted original R model.
# All model fitting, integration, population reconstruction and validation run locally.
args <- commandArgs(trailingOnly=TRUE)
arg <- function(key, default=NULL) { i <- match(key,args); if (is.na(i)) default else args[i+1L] }
job <- normalizePath(arg('--job'), winslash='/', mustWork=TRUE)
mode <- arg('--mode','smoke')
.libPaths(c(Sys.getenv('BLUEFOOD_R_LIBRARY'),file.path(job,'Rlibrary'),.libPaths()))
stopifnot(requireNamespace('deSolve',quietly=TRUE),requireNamespace('openxlsx',quietly=TRUE),requireNamespace('jsonlite',quietly=TRUE))
options(pbk.parameter_workbook=file.path(job,'original_source','Fabrega_2015_data.xlsx'))
source(file.path(job,'code','PFAS_PBK_US_2003_2016_Fabrega_2015.R'))
source(file.path(job,'code','ode_fast.R'))
original_env <- new.env(parent=globalenv())
expressions <- parse(file.path(job,'original_source','PFAS_PBK_validation_Fabrega_2015.R'))
for (e in expressions) if (is.call(e) && identical(e[[1]],as.name('<-')) && as.character(e[[2]]) %in% c('create.params','create.inits','create.events','ode.func')) eval(e,original_env)
original_env$create.params <- create.params
YEARS <- 2003:2016
dates <- as.Date(paste0(c(YEARS,2017),'-01-01'))
bounds <- as.integer(dates-dates[1])
state_retained <- c('APlas','AG','AL','AF','ALu','AB','ABm','AK','AFil','AStor','AR')
substances <- c('PFOA','PFOS')
fractions <- list(PFOA=c(aquatic=.151,terrestrial=.183),PFOS=c(aquatic=.50,terrestrial=.771))
# Historical PBK reproduction factors for food intake starting in 2005.
report_multipliers <- c(PFOA=7.656725865487441,PFOS=0.3984242389525426)
targets <- c(PFOA=3.95,PFOS=20.70)
# Fixed virtual populations; worker/grid options only control acceleration.
pop_sizes <- c(PFOA=100000L,PFOS=100000L)
stopifnot(all(pop_sizes==100000L))
scenarios <- c('no_exposure','aquatic_only','terrestrial_only','aquatic_plus_terrestrial')
out <- file.path(job,'results')
dir.create(out,showWarnings=FALSE,recursive=TRUE)
json <- function(x,path) jsonlite::write_json(x,path,pretty=TRUE,auto_unbox=TRUE,digits=16,na='null')
gm <- function(x) {stopifnot(all(is.finite(x)),all(x>0));exp(mean(log(x)))}
summary_values <- function(x) {
  stopifnot(all(is.finite(x)),all(x>=0))
  p <- quantile(x,c(.05,.10,.25,.5,.75,.90,.95),names=FALSE,type=7)
  c(geometric_mean=if(any(x==0)) 0 else gm(x),arithmetic_mean=mean(x),sd=sd(x),
    setNames(p,c('p05','p10','p25','median','p75','p90','p95')))
}
food_scenario_plan <- function(values,baseline_multiplier,compound,scenario) {
  raw_total <- values[seq(1,42,3)]
  raw_aq <- values[seq(2,42,3)]
  raw_terr <- values[seq(3,42,3)]
  aq_on <- scenario %in% c('aquatic_only','aquatic_plus_terrestrial')
  tr_on <- scenario %in% c('terrestrial_only','aquatic_plus_terrestrial')
  food_multiplier <- report_multipliers[[compound]]
  # The ODE applies each food fraction to these scaled rates once.
  cbind(water_solution=c(raw_total[1:2]*baseline_multiplier,rep(0,12)),
    aquatic=c(0,0,raw_aq[3:14]*aq_on*food_multiplier),
    terrestrial=c(0,0,raw_terr[3:14]*tr_on*food_multiplier),
    f_aqua=fractions[[compound]][['aquatic']],f_terri=fractions[[compound]][['terrestrial']])
}
parameters <- function(compound) {
  p <- create.params(list(BW=70,substance=compound,exposure=0,exposure_times=0))
  p$transport_matrix <- build_transport_matrix(p)
  p
}
equilibrium_plasma <- function(p,ngday) {
  rate <- ngday/1000/24
  cf <- rate/p$QFil
  (rate+p$Tm*cf/(p$Kt+cf))/(p$QFil*p$Free)
}
balanced_state <- function(p,ngday) {
  rate <- ngday/1000/24
  cf <- rate/p$QFil
  reabs <- p$Tm*cf/(p$Kt+cf)
  cp <- equilibrium_plasma(p,ngday)
  cg <- p$PG*(cp+rate/(p$QG*p$Free))
  cl <- p$PL*(p$QL*cp+p$QG*cg/p$PG)/(p$QL+p$QG)
  ck <- p$PK*(cp+reabs/(p$QK*p$Free))
  y <- create.inits(p)
  y[state_retained] <- c(cp*p$VPlas,cg*p$VG,cl*p$VL,p$PF*cp*p$VF,
      p$PLu*cp*p$VLu,p$PB*cp*p$VB,p$PBm*cp*p$VBm,ck*p$VK,cf*p$VFil,rate/p$kurine,p$PR*cp*p$VR)
  y['Intake'] <- rate
  y['A_in'] <- sum(y[state_retained])
  stopifnot(all(is.finite(y)),all(y>=0))
  y
}
run_path <- function(p,annual,initial_ngday,rtol=1e-8,atol=1e-10,keep_states=FALSE,output_step_days=7L,reference=FALSE) {
  y <- balanced_state(p,initial_ngday)
  cp <- numeric(tail(bounds,1)+1L)
  cp[1] <- y['APlas']/p$VPlas
  max_mass_error <- 0
  min_amount <- Inf
  # Keep the original continuous hourly input convention. Each year's rates are constant.
  for (i in seq_len(nrow(annual))) {
    y['Intake'] <- annual[i,'water_solution']/1000/24
    pp <- p
    pp$Intake_aquatic <- annual[i,'aquatic']/1000/24
    pp$Intake_terrestrial <- annual[i,'terrestrial']/1000/24
    pp$f_aqua <- annual[i,'f_aqua'];pp$f_terri <- annual[i,'f_terri'];pp$f_water <- 1
    days <- bounds[i+1L]-bounds[i]
    evaluation_days <- sort(unique(c(seq(0,days,by=output_step_days),0:min(7,days),days)))
    sol <- deSolve::ode(y=y,times=evaluation_days*24,func=if(reference)ode.func else ode.fast,parms=pp,
                       method='lsodes',rtol=rtol,atol=atol)
    stopifnot(nrow(sol)==length(evaluation_days),all(is.finite(sol)),tail(sol[,'time'],1)==days*24)
    cp[(bounds[i]+1L):(bounds[i+1L]+1L)] <- approx(evaluation_days,sol[,'CPlas'],xout=0:days)$y
    max_mass_error <- max(max_mass_error,max(abs(sol[,'Mass_Balance'])))
    min_amount <- min(min_amount,min(sol[,state_retained]))
    y <- setNames(as.numeric(tail(sol[,names(y),drop=FALSE],1)),names(y))
  }
  stopifnot(min_amount>=-1e-8,max_mass_error<1e-4,all(cp>=0))
  list(curve=cp,mass_error=max_mass_error,min_amount=min_amount,final_state=if(keep_states)y else NULL)
}

if (mode=='smoke') {
  checks <- list()
  for (compound in substances) {
    p <- parameters(compound)
    y <- create.inits(p);y['Intake'] <- 40/1000/24
    times <- c(0,1,24,240,8760,87600)
    a <- deSolve::ode(y,times,original_env$ode.func,p,method='lsodes',rtol=1e-8,atol=1e-10)
    b <- deSolve::ode(y,times,ode.func,p,method='lsodes',rtol=1e-8,atol=1e-10)
    delta <- max(abs(a-b));stopifnot(delta<1e-9)
    fast <- deSolve::ode(y,times,ode.fast,p,method='lsodes',rtol=1e-8,atol=1e-10)
    fast_curve_difference <- max(abs(fast[,'CPlas']-b[,'CPlas'])/pmax(abs(b[,'CPlas']),1e-10))
    stopifnot(fast_curve_difference<1e-5)
    set.seed(20261105)
    derivative_errors <- replicate(100,{
      yy <- setNames(runif(14,.001,10),names(y));yy['A_in'] <- sum(yy[1:12])
      qp <- p;qp$f_aqua <- runif(1);qp$f_terri <- runif(1);qp$f_water <- runif(1)
      qp$Intake_aquatic <- runif(1);qp$Intake_terrestrial <- runif(1)
      expected <- ode.func(0,yy,qp)[[1]];actual <- ode.fast(0,yy,qp)[[1]]
      max(abs(actual-expected)/pmax(1,abs(expected)))
    })
    stopifnot(max(derivative_errors)<1e-10)
    z <- balanced_state(p,40)
    pp <- p;pp$f_aqua <- .25;pp$Intake_aquatic <- 160/1000/24;pp$Intake_terrestrial <- 0
    z['Intake'] <- 0
    residual <- ode.func(0,z,pp)[[1]][match(state_retained,names(z))]
    stopifnot(max(abs(residual))<1e-8)
    zz <- create.inits(p)
    pp$f_aqua <- 0
    zzsol <- deSolve::ode(zz,c(0,24,240),ode.func,pp,method='lsodes',rtol=1e-8,atol=1e-10)
    stopifnot(max(abs(zzsol[,'CPlas']))==0,max(abs(zzsol[,'A_in']))==0)
    # Equal available input must yield the same state derivatives, including A_in.
    qa <- p;qa$Intake_aquatic <- 40/1000/24;qa$f_aqua <- .5
    qt <- p;qt$Intake_terrestrial <- 40/1000/24;qt$f_terri <- .5
    da <- ode.func(0,zz,qa)[[1]];dt <- ode.func(0,zz,qt)[[1]]
    stopifnot(max(abs(da-dt))<1e-14)
    elapsed <- system.time({test <- run_path(p,cbind(water_solution=rep(40,14),aquatic=0,terrestrial=0,f_aqua=1,f_terri=1),40)})[['elapsed']]
    checks[[compound]] <- list(original_f1_max_absolute_difference=delta,
      equilibrium_max_retained_derivative=max(abs(residual)),f0_zero_food_input_verified=TRUE,
      fraction_applied_once_verified=TRUE,mass_balance_error_ug=test$mass_error,
      continuous_equilibrium_relative_drift=max(abs(test$curve/equilibrium_plasma(p,40)-1)),
      fast_vs_original_derivative_max_scaled_error=max(derivative_errors),
      fast_vs_original_serum_curve_max_relative_error=fast_curve_difference,
      full_14_year_path_seconds=elapsed)
  }
  json(list(status='passed',checks=checks,R=R.version.string),file.path(out,'SMOKE_VERIFICATION.json'))
  print(checks)
  quit(status=0)
}

stopifnot(mode %in% c('prepare','run'))
input_root <- arg('--input-root',file.path(dirname(job),'exposure_inputs','US 2003-2016 time depend Mix_k'))
if (mode=='prepare') {
  annual <- setNames(vector('list',length(substances)),substances)
  manifest <- list();k <- 0L
  for(compound in substances) annual[[compound]] <- list()
  for (year in YEARS) for (kind in c('total','aqours','terri')) {
    path <- file.path(input_root,paste0(year,'_US_',kind,'_exposure'),'N100000_United States_expo.csv')
    x <- read.csv(path,check.names=FALSE)
    stopifnot(nrow(x)==100000L,all(substances %in% names(x)))
    for (compound in substances) {
      values <- x[[compound]]
      stopifnot(all(is.finite(values)),all(values>=0))
      annual[[compound]][[paste(year,kind,sep='_')]] <- sort(values)
    }
    k <- k+1L;manifest[[k]] <- list(path=path,md5=unname(tools::md5sum(path)),rows=nrow(x),year=year,kind=kind)
    cat('READ_INPUT',year,kind,'\n');flush.console()
  }
  saveRDS(annual,file.path(out,'annual_intake_sorted.rds'),compress=TRUE)
  json(manifest,file.path(out,'EXPOSURE_INPUT_MANIFEST.json'))
  json(list(compounds=substances,years=YEARS,population_n=as.list(pop_sizes),physiological_body_weight_kg=70,
    input_unit='ng/person/day; use raw exposure, no body-weight re-scaling',
    serum_unit='ng/mL = ug/L',oral_input='continuous hourly input as in the GitHub R script',
    food_fractions=fractions,water_solution_fraction=1,
    post2004_exposure_multiplier=as.list(report_multipliers),
    post2004_multiplier_application='Historical compound factor applied once to aquatic and terrestrial food doses from 2005 onward',
    baseline='Calibrate only 2003-2004 solution-equivalent input and equilibrium initialization to the first NHANES GM',
    scenarios=scenarios,persistence='Same exposure percentile retained across years and food branches; marginal intake files sorted separately',
    parameter_workbook=getOption('pbk.parameter_workbook')),file.path(out,'settings.json'))
  quit(status=0)
}

annual_sorted <- readRDS(file.path(out,'annual_intake_sorted.rds'))
requested <- arg('--compound',NULL)
if(!is.null(requested)) substances <- requested
grid_n <- as.integer(arg('--grid','257'))
workers <- as.integer(arg('--workers','3'))
stopifnot(workers>=1L,grid_n>=33L)
cl <- if(workers>1L) parallel::makeCluster(workers,type='PSOCK') else NULL
if(!is.null(cl)) {
  parallel::clusterExport(cl,c('job'))
  parallel::clusterEvalQ(cl,{
    .libPaths(c(Sys.getenv('BLUEFOOD_R_LIBRARY'),file.path(job,'Rlibrary'),.libPaths()))
    options(pbk.parameter_workbook=file.path(job,'original_source','Fabrega_2015_data.xlsx'))
    source(file.path(job,'code','PFAS_PBK_US_2003_2016_Fabrega_2015.R'))
    source(file.path(job,'code','ode_fast.R'))
    NULL
  })
  parallel::clusterExport(cl,c('YEARS','bounds','state_retained','balanced_state','equilibrium_plasma','run_path'))
}
map_paths <- function(jobs,p) {
  fun <- function(j,p) run_path(p,j$annual,j$initial,output_step_days=if(isTRUE(j$dense))1L else 7L,reference=isTRUE(j$reference))
  if(is.null(cl)) lapply(jobs,fun,p=p) else parallel::parLapplyLB(cl,jobs,fun,p=p)
}
make_grid <- function(n,ranks) sort(unique(c(seq(min(ranks),max(ranks),length.out=n),
  exp(seq(log(min(ranks)),log(.02),length.out=40)),1-exp(seq(log(min(ranks)),log(.02),length.out=40)))))
at_samples <- function(curves,grid,ranks,day) {
  result <- numeric(length(ranks));lower <- floor(day);frac <- day-lower
  groups <- split(seq_along(lower),lower)
  for(key in names(groups)) {
    d <- as.integer(key);idx <- groups[[key]]
    a <- splinefun(grid,curves[,d+1L],method='monoH.FC')(ranks[idx])
    b <- splinefun(grid,curves[,d+2L],method='monoH.FC')(ranks[idx])
    result[idx] <- a*(1-frac[idx])+b*frac[idx]
  }
  stopifnot(all(is.finite(result)),all(result>=0));result
}
check_curves <- function(paths,days) {
  vapply(paths,function(path) path$curve[days+1L],numeric(length(days)))
}
check_interpolation <- function(grid,curves,ranks,days,reference) {
  predicted <- t(vapply(days,function(day) {
    splinefun(grid,curves[,day+1L],method='monoH.FC')(ranks)
  },numeric(length(ranks))))
  errors <- abs(predicted-reference)/pmax(abs(reference),1e-10)
  stopifnot(all(is.finite(errors)))
  worst <- arrayInd(which.max(errors),dim(errors))[1L,]
  list(errors=errors,predicted=predicted,max_error=errors[worst[1L],worst[2L]],
       rank=ranks[worst[2L]],day=days[worst[1L]])
}
refinement_nodes <- function(grid,failing_ranks,check_ranks) {
  # Refine the bracket around each failing rank and its immediate neighbours.
  bracket <- findInterval(failing_ranks,grid)
  bracket <- sort(unique(c(bracket-1L,bracket,bracket+1L)))
  bracket <- bracket[bracket>=1L & bracket<length(grid)]
  nodes <- lapply(bracket,function(index) {
    left <- grid[index];right <- grid[index+1L]
    preferred <- left+(right-left)*c(.25,.5,.75)
    # The finer fractions supply alternatives if a preferred node hits a check rank.
    available <- unique(left+(right-left)*seq_len(31L)/32)
    collides <- vapply(available,function(node) {
      any(abs(node-check_ranks)<8*.Machine$double.eps)
    },logical(1))
    available <- available[available>left & available<right & !collides]
    selected <- numeric()
    for(target in preferred) {
      if(length(available)==0L) break
      nearest <- which.min(abs(available-target))
      selected <- c(selected,available[nearest])
      available <- available[-nearest]
    }
    selected
  })
  sort(unique(unlist(nodes,use.names=FALSE)))
}
rows_period <- list();rows_year <- list();diagnostics <- list()
bench <- read.csv(arg('--benchmark',file.path(dirname(job),'code_and_results','benchmarks','nhanes_pfas_total_population.csv')))
for(compound in substances) {
  started <- proc.time()[['elapsed']]
  p <- parameters(compound);N <- pop_sizes[[compound]]
  stopifnot(length(N)==1L,!is.na(N),N==100000L)
  ranks <- (seq_len(N)-.5)/N
  annual <- matrix(0,nrow=N,ncol=length(YEARS)*3L)
  for(i in seq_along(YEARS)) for(k in seq_len(3L)) {
    key <- paste(YEARS[i],c('total','aqours','terri')[k],sep='_')
    annual[,3L*(i-1L)+k] <- approx((seq_len(100000L)-.5)/100000,annual_sorted[[compound]][[key]],xout=ranks,rule=2)$y
  }
  initial_grid <- make_grid(grid_n,ranks)
  set.seed(if(compound=='PFOA')2601105 else 2601106)
  sample_period <- lapply(seq(1,13,2),function(i)runif(N,bounds[i],bounds[i+2L]))
  sample_year <- lapply(seq_along(YEARS),function(i)runif(N,bounds[i],bounds[i+1L]))
  baseline_plan <- function(values,m) cbind(water_solution=c(values[1:2]*m,rep(0,12)),aquatic=0,terrestrial=0,f_aqua=0,f_terri=0)
  # Root fit uses the full rank distribution for initial equilibrium, then checks the
  # actual 2003-2004 sampling window with the R ODE. No future measurement enters it.
  m <- uniroot(function(x) log(gm(equilibrium_plasma(p,annual[,1]*x))/targets[[compound]]),c(1e-5,1000),tol=1e-10)$root
  fit_grid <- make_grid(65L,ranks)
  fit_annual <- vapply(seq_len(ncol(annual)),function(i)approx(ranks,annual[,i],xout=fit_grid,rule=2)$y,numeric(length(fit_grid)))
  baseline_gm <- function(multiplier) {
    jobs <- lapply(seq_along(fit_grid),function(i)list(annual=baseline_plan(fit_annual[i,seq(1,42,3)],multiplier)[1:2,,drop=FALSE],initial=fit_annual[i,1]*multiplier))
    solved <- map_paths(jobs,p)
    curves <- do.call(rbind,lapply(solved,`[[`,'curve'))
    gm(at_samples(curves,fit_grid,ranks,sample_period[[1]]))
  }
  m <- uniroot(function(x)log(baseline_gm(x)/targets[[compound]]),c(m/2,m*2),tol=1e-8)$root
  cat('CALIBRATED_BASELINE',compound,m,'\n');flush.console()
  compound_out <- file.path(out,compound);dir.create(compound_out,showWarnings=FALSE)
  for(scenario in scenarios) {
    cat('START_SCENARIO',compound,scenario,'grid',length(initial_grid),'\n');flush.console()
    plan <- function(values) food_scenario_plan(values,m,compound,scenario)
    solve_grid <- function(nodes,dense) {
      intakes <- vapply(seq_len(ncol(annual)),function(i) {
        approx(ranks,annual[,i],xout=nodes,rule=2)$y
      },numeric(length(nodes)))
      # vapply simplifies to a vector when there is only one new node.
      intakes <- matrix(intakes,nrow=length(nodes))
      jobs <- lapply(seq_along(nodes),function(i) {
        list(annual=plan(intakes[i,]),initial=intakes[i,1]*m,dense=dense)
      })
      map_paths(jobs,p)
    }
    grid <- initial_grid;dense <- FALSE
    solved <- solve_grid(grid,dense)
    scenario_out <- file.path(compound_out,scenario);dir.create(scenario_out,showWarnings=FALSE)
    # Independent ranks validate interpolation against freshly integrated R paths.
    check_ranks <- c(.0002,.003,.0137,.087,.219,.411,.638,.831,.974,.9967,.9998)
    check_ranks <- check_ranks[check_ranks>min(ranks)&check_ranks<max(ranks)]
    check_values <- vapply(seq_len(ncol(annual)),function(i)approx(ranks,annual[,i],xout=check_ranks,rule=2)$y,numeric(length(check_ranks)))
    check_jobs <- lapply(seq_along(check_ranks),function(i)list(annual=plan(check_values[i,]),initial=check_values[i,1]*m,dense=TRUE,reference=i %in% c(2L,6L,10L)))
    exact <- map_paths(check_jobs,p)
    check_days <- sort(unique(c(seq(0,tail(bounds,1),by=91),unlist(lapply(bounds[-length(bounds)],function(d)d+0:14)))))
    reference <- check_curves(exact,check_days)
    weekly_reference <- NULL
    refinement <- list()
    max_attempts <- 7L
    for(attempt in seq_len(max_attempts)) {
      curves <- do.call(rbind,lapply(solved,`[[`,'curve'))
      validation <- check_interpolation(grid,curves,check_ranks,check_days,reference)
      max_interp <- validation$max_error
      step_days <- if(dense) 1L else 7L
      record <- list(attempt=attempt,grid_size=length(grid),output_step_days=step_days,
                     max_relative_error=max_interp,worst_rank=validation$rank,worst_day=validation$day)
      refinement[[attempt]] <- record
      if(max_interp<.01) break
      cat('REFINE_VALIDATION',compound,scenario,'attempt',attempt,'grid',length(grid),
          'step_days',step_days,'max_relative_error',max_interp,
          'rank',validation$rank,'day',validation$day,'\n');flush.console()
      if(attempt==max_attempts) break

      if(!dense) {
        if(is.null(weekly_reference)) {
          weekly_jobs <- lapply(check_jobs,function(job) { job$dense <- FALSE;job })
          weekly_reference <- check_curves(map_paths(weekly_jobs,p),check_days)
        }
        scale <- pmax(abs(reference),1e-10)
        time_error <- max(abs(weekly_reference-reference)/scale)
        rank_error <- max(abs(validation$predicted-weekly_reference)/scale)
        refinement[[attempt]]$weekly_time_max_relative_error <- time_error
        refinement[[attempt]]$weekly_rank_max_relative_error <- rank_error
        cat('VALIDATION_COMPONENTS',compound,scenario,'time',time_error,'rank',rank_error,'\n');flush.console()
        if(time_error>=.01 || time_error>=rank_error) {
          refinement[[attempt]]$action <- 'daily_output'
          dense <- TRUE
          solved <- solve_grid(grid,dense)
          next
        }
      }

      failing_ranks <- check_ranks[apply(validation$errors,2L,max)>=.01]
      new_nodes <- refinement_nodes(grid,failing_ranks,check_ranks)
      if(length(new_nodes)==0L) break
      refinement[[attempt]]$action <- 'refine_rank_brackets'
      refinement[[attempt]]$added_grid_nodes <- new_nodes
      order_nodes <- order(c(grid,new_nodes))
      solved <- c(solved,solve_grid(new_nodes,dense))[order_nodes]
      grid <- c(grid,new_nodes)[order_nodes]
    }
    mass_error <- max(vapply(c(solved,exact),`[[`,numeric(1),'mass_error'))
    saveRDS(list(grid=grid,curves=curves,baseline_multiplier=m),file.path(scenario_out,'solver_grid.rds'),compress=TRUE)
    diagnostic <- list(status=if(max_interp<.01) 'passed' else 'failed',mass_balance_max_error_ug=mass_error,
      interpolation_max_relative_error=max_interp,validation_ranks=check_ranks,grid_size=length(grid),
      requested_grid_size=grid_n,initial_grid_size=length(initial_grid),output_step_days=step_days,
      worst_validation_rank=validation$rank,worst_validation_day=validation$day,refinement=refinement,
      baseline_only_multiplier=m,post2004_multiplier=report_multipliers[[compound]],food_f=as.list(fractions[[compound]]))
    json(diagnostic,file.path(scenario_out,'verification.json'))
    if(!(max_interp<.01)) {
      stop(sprintf('%s %s interpolation validation failed: %.6g at rank %.6g, day %d (required < 0.01)',
                   compound,scenario,max_interp,validation$rank,validation$day))
    }
    for(k in seq_along(sample_period)) {
      values <- at_samples(curves,grid,ranks,sample_period[[k]])
      cycle <- paste(YEARS[2*k-1],YEARS[2*k],sep='-')
      reference <- bench$gm[bench$compound==compound&bench$cycle==cycle]
      stopifnot(length(reference)==1L)
      s <- summary_values(values)
      rows_period[[length(rows_period)+1L]] <- c(list(compound=compound,scenario=scenario,period=cycle,n=N,
         NHANES_gmean=reference,gmean_percent_difference=100*(s[['geometric_mean']]/reference-1)),as.list(s))
      con <- gzfile(file.path(scenario_out,paste0(cycle,'_population.csv.gz')),'wt')
      write.csv(data.frame(individual_id=seq_len(N),persistent_percentile=ranks,
        sampling_day=sample_period[[k]],plasma_ng_ml=values),con,row.names=FALSE)
      close(con)
    }
    for(k in seq_along(sample_year)) {
      values <- at_samples(curves,grid,ranks,sample_year[[k]])
      rows_year[[length(rows_year)+1L]] <- c(list(compound=compound,scenario=scenario,year=YEARS[k],n=N),as.list(summary_values(values)))
    }
    diagnostics[[paste(compound,scenario,sep='_')]] <- diagnostic
    cat('FINISHED_SCENARIO',compound,scenario,'mass_error',mass_error,'interpolation',max_interp,'\n');flush.console()
  }
  json(list(compound=compound,runtime_seconds=proc.time()[['elapsed']]-started,baseline_only_multiplier=m,
      post2004_multiplier=report_multipliers[[compound]],
      initial_equilibrium_GM=gm(equilibrium_plasma(p,annual[,1]*m)),n=N),file.path(compound_out,'settings.json'))
}
as_rows <- function(x) do.call(rbind,lapply(x,function(r)as.data.frame(r,stringsAsFactors=FALSE)))
periods <- as_rows(rows_period);annual_results <- as_rows(rows_year)
suffix <- if(length(substances)==1L)paste0('_',substances)else ''
write.csv(periods,file.path(out,paste0('period_results',suffix,'.csv')),row.names=FALSE)
write.csv(annual_results,file.path(out,paste0('annual_results',suffix,'.csv')),row.names=FALSE)
json(list(status='passed',compound=substances,checks=diagnostics,completed_utc=format(Sys.time(),tz='UTC',usetz=TRUE),
  future_serum_measurements_used_for_fitting=FALSE,baseline_only_calibration=TRUE,
  post2004_report_multipliers=as.list(report_multipliers[substances]),
  original_equations_preserved_except_explicit_fractional_gut_input=TRUE),file.path(out,paste0('COMPLETE',suffix,'.json')))
print(periods[,c('compound','scenario','period','geometric_mean','NHANES_gmean','gmean_percent_difference')])
if(!is.null(cl)) {parallel::stopCluster(cl);cl <- NULL}
