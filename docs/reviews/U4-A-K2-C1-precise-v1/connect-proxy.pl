use strict;
use warnings;
use IO::Socket::INET;
use IO::Select;
use POSIX qw(:sys_wait_h);
$| = 1;
my ($mode, $log, $ready) = @ARGV;
die "explicit index or archives mode required" unless $mode eq 'index' || $mode eq 'archives';
open(my $events, '>>', $log) or die $!;
select((select($events), $| = 1)[0]);
sub record {
    my @fields = @_;
    for (@fields) { $_ = '' unless defined $_; s/[\r\n\t]/ /g; }
    print $events join("\t", time(), $$, @fields), "\n";
}
my $listener = IO::Socket::INET->new(LocalAddr=>'127.0.0.1', LocalPort=>18081,
    Listen=>32, ReuseAddr=>1) or die $!;
open(my $marker, '>', $ready) or die $!;
print $marker "ready\n"; close($marker);
record('listen', '127.0.0.1', 18081, $mode);
$SIG{CHLD} = sub { while (waitpid(-1, WNOHANG) > 0) {} };
while (my $client = $listener->accept()) {
    my $pid = fork();
    die $! unless defined $pid;
    if ($pid) { close($client); next; }
    close($listener);
    my $request = '';
    while (index($request, "\r\n\r\n") < 0 && length($request) < 8192) {
        my $got = sysread($client, my $part, 1024);
        last unless $got;
        $request .= $part;
    }
    my ($host, $port) = $request =~ /^CONNECT ([a-z0-9.-]+):([0-9]+) HTTP\/1\.[01]\r\n/;
    my $allowed = defined($host) && $port == 443 &&
        ($host eq 'index.crates.io' || ($mode eq 'archives' && $host eq 'static.crates.io'));
    if (!$allowed) {
        record('denied', unpack('H*', substr($request, 0, 1024)));
        syswrite($client, "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n");
        close($client); exit(0);
    }
    my $upstream = IO::Socket::INET->new(PeerAddr=>$host, PeerPort=>443, Proto=>'tcp', Timeout=>30);
    if (!$upstream) {
        record('connect_error', $host, $port, "$!");
        syswrite($client, "HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n");
        close($client); exit(0);
    }
    record('connected', $host, $port, $upstream->peerhost());
    syswrite($client, "HTTP/1.1 200 Connection established\r\n\r\n");
    my $poll = IO::Select->new($client, $upstream);
    my ($sent, $received) = (0, 0);
    my $finish = 'closed';
    TUNNEL: while (1) {
        my @ready_sockets = $poll->can_read(60);
        if (!@ready_sockets) { $finish = 'timeout'; last; }
        for my $socket (@ready_sockets) {
            my $got = sysread($socket, my $buffer, 65536);
            last TUNNEL unless $got;
            my $from_client = fileno($socket) == fileno($client);
            my $destination = $from_client ? $upstream : $client;
            my $offset = 0;
            while ($offset < $got) {
                my $written = syswrite($destination, $buffer, $got - $offset, $offset);
                if (!$written) { $finish='write_error'; last TUNNEL; }
                $offset += $written;
            }
            if ($from_client) { $sent += $got; } else { $received += $got; }
        }
    }
    record('finished', $host, $port, $finish, $sent, $received);
    close($client); close($upstream); exit(0);
}
