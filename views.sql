create or replace view aklub_v_member_counts_by_months as
       (select
           *,
           sum(total) over (order by year, month) as run_total
       from
       (select r.y||'.'||r.m as id,
       r.y as year,
       r.m as month,
       coalesce(r.c, 0) as regular,
       coalesce(i.c, 0) as irregular,
       coalesce(r.c, 0) + coalesce (i.c, 0) as total
       from
       	    (select
		floor(extract(year from registered_support)) as y,
	    	floor(extract(month from registered_support)) as m,
		count(*) as c
		from aklub_user
		where regular_payments=true and active=true
		group by y,m)
		as r
	     left join
       	     (select
		extract(year from registered_support) as y,
	    	extract(month from registered_support) as m,
		count(*) as c
		from aklub_user
		where regular_payments=false and active=true
		group by y,m
		) as i
              on r.y=i.y and r.m=i.m
	) as c
       	order by year, month);
grant all on aklub_v_member_counts_by_months to django;

create or replace view aklub_v_payments_by_months as
       (select
           *,
           sum(total) over (order by year, month) as run_total
       from
       (select p.y||'.'||p.m as id,
       p.y as year,
       p.m as month,
       p.s as total
       from
       	    (select
		floor(extract(year from date)) as y,
	    	floor(extract(month from date)) as m,
		sum(amount) as s
		from aklub_payment
		where type != 'expected'
		group by y,m)
		as p
	) as t
       	order by year, month);
grant all on aklub_v_payments_by_months to django;

