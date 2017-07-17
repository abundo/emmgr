/**
 * 
 */

function updateJobs(id, param) {
	// console.log("updateJobs");
	$.ajax({
		dataType : "json",
		url : "/api/jobs" + param,
		success : function(result) {
			console.log(result);
			html = "";
			$.each(result["jobs"], function(ix, job) {
				html += "<tr>"
				html += "<td><a href='/jobs/status/" + job["id"] + "'>" + job["id"] + "</a></td>\n";
				html += "<td>" + job["description"] + "</td>\n";
				html += "<td>" + job["status"] + "</td>\n";
				html += "<td>" + job["statusinfo"] + "</td>\n";
				html += "<td>" + job["created"] + "</td>\n";
				html += "</tr>"
			});
			$(id).html(html);
		},
		
	});
}

function startPeriodUpdateJobs() {
	updateJobs("#id_jobs_active tbody", "");
	updateJobs("#id_jobs_completed tbody", "?inactive=1");
	setTimeout(startPeriodUpdateJobs, 2000);			
}

function startPeriodUpdateJob(job_id, id_job, id_subjob) {
	$.ajax({
		dataType : "json",
		url : "/api/jobs/" + job_id,
		success : function(result) {
			// console.log(result);
			html = "";
			job = result['job'];
			console.log("job", job);
			if (jQuery.isEmptyObject(job)) {
	   	    	window.location.href = "/jobs/status";
			}
			html += "<tr>"
			html += "<td>" + job["description"] + "</td>\n";
			html += "<td>" + job["status"] + "</td>\n";
			html += "<td>" + job["statusinfo"] + "</td>\n";
			html += "<td>" + job["created"] + "</td>\n";
			html += "<td>" + job["current"] + "</td>\n";
			html += "<td>" + job["submitter"] + "</td>\n";
			html += "<td>" + job["result"] + "</td>\n";
			html += "</tr>"
			$(id_job + " tbody").html(html);

			html = "";
			$.each(result["job"]["subjob"], function(ix, subjob) {
				// console.log(ix, subjob);
				html += "<tr>"
				html += "<td>" + subjob["id"] + "</td>\n";
				html += "<td>" + subjob["action"] + "</td>\n";
				html += "<td>" + subjob["status"] + "</td>\n";
				html += "<td>" + subjob["statusinfo"] + "</td>\n";
				html += "<td>" + subjob["result"] + "</td>\n";
				html += "<td style='word-wrap: break-word;white-space:normal;'>" + JSON.stringify(subjob["args"]) + "</td>\n";
				html += "</tr>"
			});
			$(id_subjob + " tbody").html(html);
		},
	});

	setTimeout( function() {
		startPeriodUpdateJob(job_id, id_job, id_subjob);
	}, 2000);
}
